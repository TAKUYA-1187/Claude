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
    return order_id.startswith("000-")


async def save_screenshot(page, name: str) -> None:
    path = SCRIPT_DIR / f"debug_{name}.png"
    await page.screenshot(path=str(path), full_page=True)
    logger.info(f"  スクリーンショット: {path}")


async def login(page) -> bool:
    """
    セラーセントラルへのログイン。
    保存済みセッションがあれば自動スキップ。
    未ログインの場合はブラウザで手動ログインを促す。
    """
    logger.info("セラーセントラルにアクセス中...")
    await page.goto(SELLER_CENTRAL_URL, wait_until="networkidle")
    await page.wait_for_timeout(2000)

    # すでにログイン済みか確認
    if "sellercentral.amazon.co.jp" in page.url and "signin" not in page.url:
        logger.info("ログイン済みです（セッション再利用）")
        return True

    # 自動ログイン試行
    logger.info("自動ログインを試みます...")
    try:
        email_field = await page.query_selector("#ap_email")
        if email_field:
            await email_field.fill(EMAIL)
            await page.click("#continue")
            await page.wait_for_timeout(1500)

        password_field = await page.query_selector("#ap_password")
        if password_field:
            await password_field.fill(PASSWORD)
            await page.click("#signInSubmit")
            await page.wait_for_timeout(3000)
    except Exception as e:
        logger.warning(f"自動ログイン中にエラー: {e}")

    # OTP処理
    for otp_sel in ["#auth-mfa-otpcode", "#otp", "input[name='otpCode']"]:
        otp_field = await page.query_selector(otp_sel)
        if otp_field:
            logger.warning("二段階認証が必要です")
            otp = input(">>> スマホに届いたOTPコードを入力してEnter: ").strip()
            await otp_field.fill(otp)
            submit = await page.query_selector("#auth-signin-button, [type=submit]")
            if submit:
                await submit.click()
            await page.wait_for_timeout(3000)
            break

    # 自動ログイン成功確認
    if "sellercentral.amazon.co.jp" in page.url and "signin" not in page.url.lower():
        logger.info("自動ログイン成功")
        return True

    # 自動ログイン失敗 → 手動ログインを促す
    logger.warning("自動ログインに失敗しました。")
    logger.warning(">>> 開いたブラウザで手動でログインしてください。")
    logger.warning(">>> ログイン完了後、このターミナルでEnterを押してください。")
    input(">>> ログイン完了したらEnterを押してください: ")
    await page.wait_for_timeout(2000)

    if "sellercentral.amazon.co.jp" in page.url and "signin" not in page.url.lower():
        logger.info("手動ログイン確認OK")
        return True

    logger.error(f"ログイン失敗: {page.url}")
    return False


async def get_orders_for_asin(page, asin: str) -> list:
    """指定ASINの注文IDをorders-v3検索ページから取得する。"""
    search_url = f"{SELLER_CENTRAL_URL}/orders-v3/search?q={asin}&qt=asin"
    logger.info(f"  検索: {search_url}")
    await page.goto(search_url, wait_until="networkidle")
    await page.wait_for_timeout(3000)

    content = await page.content()
    order_ids = list(set(re.findall(r"\d{3}-\d{7}-\d{7}", content)))
    await save_screenshot(page, f"search_{asin}")
    return order_ids


async def send_via_messaging_compose(page, order_id: str) -> bool:
    """
    メッセージ作成URLへ直接遷移して送信する。
    複数のURLパターンを試みる。
    """
    compose_urls = [
        f"{SELLER_CENTRAL_URL}/messaging/compose?orderID={order_id}",
        f"{SELLER_CENTRAL_URL}/cu/messaging/compose?orderID={order_id}",
        f"{SELLER_CENTRAL_URL}/gp/communication-manager/inbox.html?orderId={order_id}",
    ]

    for url in compose_urls:
        logger.info(f"  メッセージ作成URL試行: {url}")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        textarea = await page.query_selector("textarea")
        if textarea:
            logger.info(f"  メッセージ入力欄を検出 → 送信処理へ")
            return await fill_and_send(page, order_id)

    return False


async def send_via_order_detail(page, order_id: str) -> bool:
    """
    注文詳細ページから「購入者に連絡」ボタンを探して送信する。
    orders-v3?page=1 の一覧から対象注文をクリックする方式も試みる。
    """
    # 方法A: 注文詳細ページへ直接遷移
    detail_url = f"{SELLER_CENTRAL_URL}/orders-v3/order/{order_id}"
    await page.goto(detail_url, wait_until="networkidle")
    await page.wait_for_timeout(3000)
    await save_screenshot(page, f"detail_{order_id.replace('-', '_')}")

    # 方法B: orders-v3一覧ページで注文行をクリック（ユーザーが確認した動作方式）
    if not await _find_and_click_contact(page, order_id):
        list_url = f"{SELLER_CENTRAL_URL}/orders-v3?page=1"
        logger.info(f"  一覧ページから注文を探す: {list_url}")
        await page.goto(list_url, wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 注文IDが含まれる行をクリック
        order_row = await page.query_selector(f"text={order_id}")
        if order_row:
            await order_row.click()
            await page.wait_for_timeout(2000)
            await save_screenshot(page, f"list_clicked_{order_id.replace('-', '_')}")

    return await _find_and_click_contact(page, order_id)


async def _find_and_click_contact(page, order_id: str) -> bool:
    """ページ上の「購入者に連絡」要素を探してクリックし、送信フォームへ進む。"""

    # 1. テキストで直接探す
    for selector in [
        "a:has-text('購入者に連絡')",
        "button:has-text('購入者に連絡')",
        "a:has-text('購入者へ連絡')",
        "span:has-text('購入者に連絡')",
        "a:has-text('Contact buyer')",
        "a:has-text('Contact Buyer')",
        "li:has-text('購入者に連絡') a",
        "li:has-text('購入者に連絡') button",
    ]:
        el = await page.query_selector(selector)
        if el:
            logger.info(f"  連絡ボタン検出: {selector}")
            await el.click()
            await page.wait_for_timeout(2000)
            # フォームが開いたか確認
            if await page.query_selector("textarea"):
                return await fill_and_send(page, order_id)

    # 2. アクションドロップダウンを開いて探す
    for dd_sel in [
        "button:has-text('アクション')",
        "button:has-text('Actions')",
        ".a-dropdown-trigger",
        "[data-action='dropdown-trigger']",
        "button.a-button-dropdown",
        "span.a-dropdown-prompt",
    ]:
        dd = await page.query_selector(dd_sel)
        if dd:
            logger.info(f"  ドロップダウン開く: {dd_sel}")
            await dd.click()
            await page.wait_for_timeout(1000)
            for contact_sel in [
                "a:has-text('購入者に連絡')",
                "a:has-text('Contact buyer')",
                "li:has-text('購入者に連絡')",
            ]:
                item = await page.query_selector(contact_sel)
                if item:
                    await item.click()
                    await page.wait_for_timeout(2000)
                    if await page.query_selector("textarea"):
                        return await fill_and_send(page, order_id)

    # 3. href に messaging/contact を含むリンクを探す
    links = await page.query_selector_all("a[href]")
    for link in links:
        href = await link.get_attribute("href") or ""
        if any(kw in href.lower() for kw in ["messaging", "contact-buyer", "contactbuyer", "contact_buyer"]):
            text = (await link.inner_text()).strip()
            logger.info(f"  連絡リンク(href): '{text}' -> {href}")
            full_url = href if href.startswith("http") else SELLER_CENTRAL_URL + href
            await page.goto(full_url, wait_until="networkidle")
            await page.wait_for_timeout(2000)
            if await page.query_selector("textarea"):
                return await fill_and_send(page, order_id)

    # デバッグ: ページ上の全リンクをログ出力
    logger.warning(f"  購入者連絡ボタンが見つかりません: {order_id}")
    all_links = await page.query_selector_all("a")
    for link in all_links:
        text = (await link.inner_text()).strip()
        href = await link.get_attribute("href") or ""
        if text and len(text) < 30:
            logger.info(f"    [DEBUG] '{text}' -> {href[:100]}")

    return False


async def fill_and_send(page, order_id: str) -> bool:
    """メッセージフォームに本文を入力して送信する。"""
    await save_screenshot(page, f"form_{order_id.replace('-', '_')}")

    # 件名ドロップダウン（ある場合）
    subject_dd = await page.query_selector("select[name*='subject'], select[id*='subject'], select[name*='reason']")
    if subject_dd:
        options = await subject_dd.query_selector_all("option")
        for opt in options:
            val = await opt.get_attribute("value") or ""
            text = (await opt.inner_text()).lower()
            if any(kw in text for kw in ["追加", "製品", "情報", "その他", "additional", "product", "other", "inquiry"]):
                await subject_dd.select_option(value=val)
                logger.info(f"  件名選択: {await opt.inner_text()}")
                break

    # メッセージ入力欄
    textarea = await page.query_selector(
        "textarea[name*='message'], textarea[id*='message'], textarea[name*='body'], textarea"
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

    if DRY_RUN:
        logger.info(f"  [DRY-RUN] フォーム入力完了。送信はスキップ: {order_id}")
        await save_screenshot(page, f"dryrun_{order_id.replace('-', '_')}")
        return True

    # 送信ボタン
    for sel in [
        "button:has-text('送信')",
        "input[type=submit][value*='送信']",
        "button:has-text('Send')",
        "button:has-text('送信する')",
        "button[type=submit]",
        "input[type=submit]",
    ]:
        btn = await page.query_selector(sel)
        if btn:
            await btn.click()
            await page.wait_for_timeout(3000)
            await save_screenshot(page, f"sent_{order_id.replace('-', '_')}")
            logger.info(f"  メッセージ送信完了: {order_id}")
            return True

    logger.warning(f"  送信ボタンが見つかりません: {order_id}")
    return False


async def send_message_to_order(page, order_id: str) -> bool:
    """購入者へのメッセージ送信。複数の方法を順に試みる。"""

    # 方法1: メッセージ作成URLへ直接遷移
    if await send_via_messaging_compose(page, order_id):
        return True

    # 方法2: 注文詳細 / 注文一覧から連絡ボタンを探す
    if await send_via_order_detail(page, order_id):
        return True

    logger.error(f"  すべての送信方法が失敗しました: {order_id}")
    return False


async def main():
    logger.info("=" * 60)
    logger.info("Amazon購入者 取扱説明書メッセージ送信 開始")
    logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"モード: {'[DRY-RUN] 確認のみ' if DRY_RUN else '[LIVE] 実際に送信'}")

    sent_orders = load_sent_orders()
    logger.info(f"送信済み注文数: {len(sent_orders)}")

    # ログインセッションをローカルに保存（初回のみ手動ログインが必要）
    USER_DATA_DIR = SCRIPT_DIR / "chrome_session"

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            channel="chrome",
            headless=False,
            locale="ja-JP",
            args=["--lang=ja-JP"],
        )
        page = await context.new_page()

        try:
            if not await login(page):
                logger.error("ログイン失敗。終了します。")
                return

            sent_count = 0
            skip_count = 0
            error_count = 0
            processed: set = set()

            for asin in TARGET_ASINS:
                logger.info(f"ASIN {asin} の注文を検索中...")
                order_ids = await get_orders_for_asin(page, asin)
                logger.info(f"  取得注文数: {len(order_ids)}")

                for order_id in order_ids:
                    if is_test_order(order_id):
                        logger.info(f"  スキップ（テスト注文）: {order_id}")
                        continue

                    if order_id in sent_orders or order_id in processed:
                        logger.info(f"  スキップ（送信済み）: {order_id}")
                        skip_count += 1
                        continue

                    processed.add(order_id)
                    logger.info(f"  送信処理: {order_id}")

                    if await send_message_to_order(page, order_id):
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
            await context.close()

    logger.info(
        f"処理完了 - 送信: {sent_count}件 / スキップ: {skip_count}件 / エラー: {error_count}件"
    )
    if DRY_RUN:
        logger.info("※ DRY_RUN=True のため実際には送信していません。")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
