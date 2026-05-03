#!/usr/bin/env python3
"""
Amazon Seller Central - 購入者への取扱説明書メッセージ自動送信（ブラウザ自動化版）
ローカルPC上で実行してください。
必要: pip install playwright && python -m playwright install chromium
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Playwrightが未インストールです。次を実行してください:")
    print("  pip install playwright")
    print("  python -m playwright install chromium")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
SENT_ORDERS_FILE = SCRIPT_DIR / "sent_orders.json"
LOG_FILE = SCRIPT_DIR / "amazon_message.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ===================== 設定 =====================
EMAIL = "taku.ino.19811014@gmail.com"
PASSWORD = "takuya1178"

# True: 動作確認のみ（実際には送信しない）  False: 実際に送信する
DRY_RUN = False

TARGET_ASINS = {
    "B0G1B3LND1",
    "B0G19VXNCJ",
    "B0G1B2J9Q9",
    "B0G1B4QN85",
}

SELLER_CENTRAL_URL = "https://sellercentral.amazon.co.jp"

MESSAGE_TEXT = """大変お世話になっております。
この度は当店の商品をご購入いただき、誠にありがとうございます。
本製品には取扱説明書を同梱しておりますが、より分かりやすくご確認いただける補足資料につきまして、同梱ができておりませんでしたため、PDF版の取扱説明書をお送りいたします。
組み立て時に迷いやすい下記の内容を中心に、詳細を記載しております。
・伸縮ポールは1本で内部に収納されている構造
・ポールの向き(黒い樹脂側が脚部側)
・天板が下がらない場合の操作方法
また、組み立て時によくある事象として、
支柱内部のポール(内筒)が入り込んでいる状態では、脚部側のネジが届かず取り付けできない場合がございます。
本製品はガス圧式の構造のため、内筒は手で引き出すことができません。
その場合は、先に天板側の昇降レバーを取り付けていただくことで、内部の支柱が作動し、内筒が適正位置まで出てまいります。
その後、脚部の取り付けを行っていただくことで、問題なく組み立てが可能となります。
上記の手順につきましても、PDF内で詳しくご案内しておりますので、あわせてご確認いただけますと幸いです。
なお、本製品はガス圧式の特性により、初期状態では昇降時にやや抵抗を感じる場合がございますが、数回操作いただくことでスムーズに動作するようになります。
万が一、組み立てやご使用にあたりご不明点がございましたら、Amazonの購入履歴よりお気軽にご連絡ください。
何卒よろしくお願い申し上げます。
▼取扱説明書(PDF)
https://1drv.ms/b/c/c37e10a4e80c2802/IQBLXIJ1RYeaRp8HRHS4EKs-Ab1_D0p3A0M0jzIK0MJ0TSM?e=fjybm7"""
# ================================================


def load_sent_orders() -> set:
    if not SENT_ORDERS_FILE.exists():
        return set()
    with open(SENT_ORDERS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("sent_orders", []))


def save_sent_orders(sent_orders: set) -> None:
    data = {
        "sent_orders": sorted(list(sent_orders)),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    with open(SENT_ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_test_order(order_id: str) -> bool:
    """Amazonのテスト注文IDを判定する（000-で始まるものは除外）。"""
    return order_id.startswith("000-")


async def login(page) -> bool:
    """セラーセントラルにログインする。OTPが必要な場合はコンソールで入力を促す。"""
    logger.info("セラーセントラルにアクセス中...")
    await page.goto(SELLER_CENTRAL_URL, wait_until="networkidle")

    if "sellercentral.amazon.co.jp" in page.url and "signin" not in page.url:
        logger.info("すでにログイン済みです")
        return True

    try:
        await page.wait_for_selector("#ap_email", timeout=10000)
        await page.fill("#ap_email", EMAIL)
        await page.click("#continue")
        await page.wait_for_timeout(1500)
    except PlaywrightTimeout:
        logger.error("ログインページのメールフィールドが見つかりません")
        return False

    try:
        await page.wait_for_selector("#ap_password", timeout=8000)
        await page.fill("#ap_password", PASSWORD)
        await page.click("#signInSubmit")
        await page.wait_for_timeout(3000)
    except PlaywrightTimeout:
        logger.error("パスワードフィールドが見つかりません")
        return False

    if await page.query_selector("#auth-mfa-otpcode") or await page.query_selector("#otp"):
        logger.warning("二段階認証が必要です")
        otp = input("スマホ/メールに届いたOTPコードを入力してください: ").strip()
        otp_field = await page.query_selector("#auth-mfa-otpcode") or await page.query_selector("#otp")
        if otp_field:
            await otp_field.fill(otp)
            submit = await page.query_selector("#auth-signin-button") or await page.query_selector("[type=submit]")
            if submit:
                await submit.click()
            await page.wait_for_timeout(3000)

    if "sellercentral.amazon.co.jp" in page.url and "signin" not in page.url.lower():
        logger.info("ログイン成功")
        return True
    else:
        logger.error(f"ログイン失敗。現在のURL: {page.url}")
        return False


async def get_orders_for_asin(page, asin: str) -> list:
    """指定ASINの注文一覧を取得する。ページ全体から注文IDを正規表現で抽出。"""
    search_url = f"{SELLER_CENTRAL_URL}/orders-v3/search?q={asin}&qt=asin"
    logger.info(f"  検索URL: {search_url}")
    await page.goto(search_url, wait_until="networkidle")
    await page.wait_for_timeout(3000)

    content = await page.content()
    order_ids = list(set(re.findall(r"\d{3}-\d{7}-\d{7}", content)))

    screenshot_path = SCRIPT_DIR / f"debug_{asin}.png"
    await page.screenshot(path=str(screenshot_path))
    logger.info(f"  スクリーンショット保存: {screenshot_path}")

    if not order_ids:
        logger.info(f"  注文が見つかりませんでした（ASIN: {asin}）")

    return order_ids


async def find_contact_link(page, order_id: str) -> tuple:
    """
    注文詳細ページから「購入者に連絡」リンクを探す。
    Returns: (element_or_None, url_or_None, found_method)
    """
    # ページ上の全リンクを収集してデバッグログに出力
    content = await page.content()
    all_hrefs = re.findall(r'href=["\']([^"\']+)["\']', content)

    # messagingやcontact関連のURLを抽出
    contact_urls = [
        h for h in all_hrefs
        if any(kw in h.lower() for kw in ["messaging", "contact", "buyer", "message"])
    ]
    logger.info(f"  [DEBUG] 連絡関連URL候補: {contact_urls[:5]}")

    # リンクテキストで「購入者」「連絡」「Contact」を含むものを列挙
    links = await page.query_selector_all("a")
    for link in links:
        text = (await link.inner_text()).strip()
        href = await link.get_attribute("href") or ""
        if text:
            logger.info(f"  [DEBUG] リンク: '{text[:40]}' -> {href[:80]}")

    # --- 方法1: テキストで探す ---
    text_selectors = [
        "a:has-text('購入者に連絡')",
        "a:has-text('購入者へ連絡')",
        "button:has-text('購入者に連絡')",
        "a:has-text('Contact buyer')",
        "a:has-text('Contact Buyer')",
        "a:has-text('Buyer')",
        "span:has-text('購入者に連絡')",
    ]
    for sel in text_selectors:
        el = await page.query_selector(sel)
        if el:
            href = await el.get_attribute("href") or ""
            logger.info(f"  連絡リンク検出（テキスト）: '{sel}' -> {href}")
            return el, href, f"text:{sel}"

    # --- 方法2: hrefのキーワードで探す ---
    href_keywords = ["messaging", "contact-buyer", "contactBuyer", "contact_buyer", "buyer-message"]
    for link in links:
        href = await link.get_attribute("href") or ""
        if any(kw in href.lower() for kw in href_keywords):
            text = (await link.inner_text()).strip()
            logger.info(f"  連絡リンク検出（href）: '{text}' -> {href}")
            return link, href, f"href:{href}"

    # --- 方法3: HTMLから直接URLを抽出して直接遷移 ---
    for url in contact_urls:
        if any(kw in url.lower() for kw in ["messaging", "contact-buyer", "contactBuyer"]):
            full_url = url if url.startswith("http") else SELLER_CENTRAL_URL + url
            logger.info(f"  連絡URL直接抽出: {full_url}")
            return None, full_url, "direct_url"

    return None, None, "not_found"


async def send_message_to_order(page, order_id: str) -> bool:
    """注文の購入者にメッセージを送信する（DRY_RUN=Trueの場合はログのみ）。"""
    order_url = f"{SELLER_CENTRAL_URL}/orders-v3/order/{order_id}"
    logger.info(f"  注文詳細ページへ: {order_url}")
    await page.goto(order_url, wait_until="networkidle")
    await page.wait_for_timeout(3000)

    # 注文詳細ページのスクリーンショット
    ss_path = SCRIPT_DIR / f"debug_order_{order_id.replace('-', '_')}.png"
    await page.screenshot(path=str(ss_path), full_page=True)
    logger.info(f"  注文詳細スクリーンショット: {ss_path}")

    el, contact_url, method = await find_contact_link(page, order_id)

    if method == "not_found":
        logger.warning(f"  [!] 購入者連絡リンクが見つかりません: {order_id}")
        if DRY_RUN:
            logger.info(f"  [DRY-RUN] 送信スキップ（ボタン未検出）: {order_id}")
        return False

    if DRY_RUN:
        logger.info(f"  [DRY-RUN] 連絡ボタン検出OK（方法: {method}）")
        logger.info(f"  [DRY-RUN] 送信予定の注文: {order_id}")
        logger.info(f"  [DRY-RUN] メッセージ冒頭: {MESSAGE_TEXT[:60]}...")
        return True

    # --- 実際の送信（DRY_RUN=False のとき） ---
    if el:
        await el.click()
    elif contact_url:
        await page.goto(contact_url, wait_until="networkidle")
    await page.wait_for_timeout(2000)

    # スクリーンショット（メッセージ入力ページ）
    ss_msg_path = SCRIPT_DIR / f"debug_msg_{order_id.replace('-', '_')}.png"
    await page.screenshot(path=str(ss_msg_path), full_page=True)
    logger.info(f"  メッセージページスクリーンショット: {ss_msg_path}")

    # 件名ドロップダウン（存在する場合）
    subject_dd = await page.query_selector("select[name*='subject'], select[id*='subject']")
    if subject_dd:
        options = await subject_dd.query_selector_all("option")
        for opt in options:
            opt_text = (await opt.inner_text()).lower()
            if any(kw in opt_text for kw in ["追加", "製品", "情報", "その他", "additional", "product", "other"]):
                val = await opt.get_attribute("value")
                await subject_dd.select_option(value=val)
                break

    # メッセージ入力欄
    textarea = await page.query_selector(
        "textarea[name*='message'], textarea[id*='message'], textarea.message-body, textarea"
    )
    if not textarea:
        textareas = await page.query_selector_all("textarea")
        textarea = textareas[-1] if textareas else None

    if not textarea:
        logger.warning(f"  メッセージ入力欄が見つかりません: {order_id}")
        return False

    await textarea.click()
    await textarea.fill(MESSAGE_TEXT)
    await page.wait_for_timeout(1000)

    # 送信ボタン
    for sel in [
        "button[type=submit]:has-text('送信')",
        "input[type=submit][value*='送信']",
        "button:has-text('Send')",
        "button:has-text('送信')",
        "button[type=submit]",
        "input[type=submit]",
    ]:
        btn = await page.query_selector(sel)
        if btn:
            await btn.click()
            await page.wait_for_timeout(3000)
            logger.info(f"  メッセージ送信完了: {order_id}")
            return True

    logger.warning(f"  送信ボタンが見つかりません: {order_id}")
    return False


async def main():
    logger.info("=" * 60)
    logger.info(f"Amazon購入者 取扱説明書メッセージ送信 開始")
    logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"モード: {'[DRY-RUN] 確認のみ（送信しない）' if DRY_RUN else '[LIVE] 実際に送信'}")

    sent_orders = load_sent_orders()
    logger.info(f"送信済み注文数: {len(sent_orders)}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--lang=ja-JP"],
        )
        context = await browser.new_context(locale="ja-JP")
        page = await context.new_page()

        try:
            if not await login(page):
                logger.error("ログインに失敗しました。終了します。")
                return

            sent_count = 0
            skip_count = 0
            error_count = 0
            processed_orders: set = set()  # ASIN間の重複処理を防ぐ

            for asin in TARGET_ASINS:
                logger.info(f"ASIN {asin} の注文を検索中...")
                order_ids = await get_orders_for_asin(page, asin)
                logger.info(f"  取得注文数: {len(order_ids)}")

                for order_id in order_ids:
                    # テスト注文を除外
                    if is_test_order(order_id):
                        logger.info(f"  スキップ（テスト注文）: {order_id}")
                        continue

                    # 送信済み・処理済みをスキップ
                    if order_id in sent_orders or order_id in processed_orders:
                        logger.info(f"  スキップ（送信済み/処理済み）: {order_id}")
                        skip_count += 1
                        continue

                    processed_orders.add(order_id)
                    logger.info(f"  処理中: {order_id}")

                    success = await send_message_to_order(page, order_id)
                    if success:
                        if not DRY_RUN:
                            sent_orders.add(order_id)
                            save_sent_orders(sent_orders)
                        sent_count += 1
                    else:
                        error_count += 1

                    await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"予期せぬエラー: {e}", exc_info=True)
        finally:
            await browser.close()

    mode = "DRY-RUN確認" if DRY_RUN else "送信"
    logger.info(f"処理完了 - {mode}: {sent_count}件 / スキップ: {skip_count}件 / エラー: {error_count}件")
    if DRY_RUN:
        logger.info("※ DRY_RUN=True のため実際には送信していません。")
        logger.info("  送信する場合は DRY_RUN = False に変更して再実行してください。")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
