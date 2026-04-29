#!/usr/bin/env python3
"""
Amazon Seller Central - 購入者への取扱説明書メッセージ自動送信（ブラウザ自動化版）
ローカルPC上で実行してください。
必要: pip install playwright && python -m playwright install chromium
"""

import asyncio
import json
import logging
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

TARGET_ASINS = {
    "B0G1B3LND1",
    "B0G19VXNCJ",
    "B0G1B2J9Q9",
    "B0G1B4QN85",
}

SELLER_CENTRAL_URL = "https://sellercentral.amazon.co.jp"

MESSAGE_SUBJECT = "取扱説明書PDFのご案内"

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


async def login(page) -> bool:
    """セラーセントラルにログインする。OTPが必要な場合はコンソールで入力を促す。"""
    logger.info("セラーセントラルにアクセス中...")
    await page.goto(SELLER_CENTRAL_URL, wait_until="networkidle")

    # すでにログイン済みか確認
    if "sellercentral.amazon.co.jp" in page.url and "signin" not in page.url:
        logger.info("すでにログイン済みです")
        return True

    # メールアドレス入力
    try:
        await page.wait_for_selector("#ap_email", timeout=10000)
        await page.fill("#ap_email", EMAIL)
        await page.click("#continue")
        await page.wait_for_timeout(1500)
    except PlaywrightTimeout:
        logger.error("ログインページのメールフィールドが見つかりません")
        return False

    # パスワード入力
    try:
        await page.wait_for_selector("#ap_password", timeout=8000)
        await page.fill("#ap_password", PASSWORD)
        await page.click("#signInSubmit")
        await page.wait_for_timeout(3000)
    except PlaywrightTimeout:
        logger.error("パスワードフィールドが見つかりません")
        return False

    # OTP（二段階認証）の処理
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

    # ログイン成功確認
    if "sellercentral.amazon.co.jp" in page.url and "signin" not in page.url.lower():
        logger.info("ログイン成功")
        return True
    else:
        logger.error(f"ログイン失敗。現在のURL: {page.url}")
        return False


async def get_orders_for_asin(page, asin: str) -> list:
    """指定ASINの注文一覧を取得する。ページ全体から注文IDを正規表現で抽出。"""
    import re

    search_url = (
        f"{SELLER_CENTRAL_URL}/orders-v3/search"
        f"?q={asin}&qt=asin"
    )
    logger.info(f"  検索URL: {search_url}")
    await page.goto(search_url, wait_until="networkidle")
    await page.wait_for_timeout(3000)

    # ページ全体のHTMLから注文IDパターン(XXX-XXXXXXX-XXXXXXX)を抽出
    content = await page.content()
    order_ids = list(set(re.findall(r"\d{3}-\d{7}-\d{7}", content)))

    # デバッグ用スクリーンショット
    screenshot_path = SCRIPT_DIR / f"debug_{asin}.png"
    await page.screenshot(path=str(screenshot_path))
    logger.info(f"  スクリーンショット保存: {screenshot_path}")

    if not order_ids:
        logger.info(f"  注文が見つかりませんでした（ASIN: {asin}）")

    return order_ids


async def send_message_to_order(page, order_id: str) -> bool:
    """注文の購入者にメッセージを送信する。"""
    # 注文詳細ページへ
    order_url = f"{SELLER_CENTRAL_URL}/orders-v3/order/{order_id}"
    await page.goto(order_url, wait_until="networkidle")
    await page.wait_for_timeout(2000)

    # 「購入者へ連絡」ボタンを探す
    contact_selectors = [
        "a[href*='messaging']:not([href*='list'])",
        "a:has-text('購入者へ連絡')",
        "a:has-text('Contact buyer')",
        "[data-action='contact-buyer']",
        "a[href*='contact-buyer']",
    ]

    contact_link = None
    for sel in contact_selectors:
        el = await page.query_selector(sel)
        if el:
            contact_link = el
            break

    if not contact_link:
        # ページ内のリンクからmessagingを探す
        links = await page.query_selector_all("a")
        for link in links:
            href = await link.get_attribute("href") or ""
            text = (await link.inner_text()).strip()
            if "messaging" in href or "contact" in href.lower() or "購入者" in text:
                contact_link = link
                break

    if not contact_link:
        logger.warning(f"購入者連絡ボタンが見つかりません: {order_id}")
        return False

    await contact_link.click()
    await page.wait_for_timeout(2000)

    # メッセージ件名の選択（ドロップダウンがある場合）
    subject_selector = await page.query_selector("select[name*='subject'], select[id*='subject']")
    if subject_selector:
        options = await subject_selector.query_selector_all("option")
        # 「追加情報」「その他」「製品について」などの選択肢を選ぶ
        target_keywords = ["追加", "製品", "情報", "その他", "additional", "product", "other"]
        for opt in options:
            opt_text = (await opt.inner_text()).lower()
            if any(kw.lower() in opt_text for kw in target_keywords):
                val = await opt.get_attribute("value")
                await subject_selector.select_option(value=val)
                break

    # メッセージ本文を入力
    textarea = await page.query_selector("textarea[name*='message'], textarea[id*='message'], textarea.message-body")
    if not textarea:
        textareas = await page.query_selector_all("textarea")
        if textareas:
            textarea = textareas[-1]

    if not textarea:
        logger.warning(f"メッセージ入力欄が見つかりません: {order_id}")
        return False

    await textarea.click()
    await textarea.fill(MESSAGE_TEXT)
    await page.wait_for_timeout(1000)

    # 送信ボタンをクリック
    send_selectors = [
        "button[type=submit]:has-text('送信')",
        "input[type=submit][value*='送信']",
        "button:has-text('Send')",
        "button[type=submit]",
        "input[type=submit]",
    ]
    sent = False
    for sel in send_selectors:
        btn = await page.query_selector(sel)
        if btn:
            await btn.click()
            await page.wait_for_timeout(3000)
            sent = True
            break

    if sent:
        logger.info(f"メッセージ送信完了: {order_id}")
        return True
    else:
        logger.warning(f"送信ボタンが見つかりません: {order_id}")
        return False


async def main():
    logger.info("=" * 60)
    logger.info("Amazon購入者 取扱説明書メッセージ送信 開始")
    logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    sent_orders = load_sent_orders()
    logger.info(f"送信済み注文数: {len(sent_orders)}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # 動作確認のためウィンドウを表示（安定したらTrueに変更可）
            args=["--lang=ja-JP"],
        )
        context = await browser.new_context(locale="ja-JP")
        page = await context.new_page()

        try:
            # ログイン
            if not await login(page):
                logger.error("ログインに失敗しました。終了します。")
                return

            sent_count = 0
            error_count = 0

            # 各ASINの注文を処理
            for asin in TARGET_ASINS:
                logger.info(f"ASIN {asin} の注文を検索中...")
                order_ids = await get_orders_for_asin(page, asin)
                logger.info(f"  取得注文数: {len(order_ids)}")

                for order_id in order_ids:
                    if order_id in sent_orders:
                        logger.info(f"  スキップ(送信済み): {order_id}")
                        continue

                    logger.info(f"  メッセージ送信中: {order_id}")
                    if await send_message_to_order(page, order_id):
                        sent_orders.add(order_id)
                        save_sent_orders(sent_orders)
                        sent_count += 1
                    else:
                        error_count += 1

                    await asyncio.sleep(2)  # 連続送信を避ける待機

        except Exception as e:
            logger.error(f"予期せぬエラー: {e}", exc_info=True)
        finally:
            await browser.close()

    logger.info(
        f"処理完了 - 送信: {sent_count}件 / エラー: {error_count}件"
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
