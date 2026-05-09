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
MARKETPLACE_ID = "A1VC38T7YXB528"  # Amazon.co.jp

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
    logger.info("セラーセントラルにアクセス中...")
    await page.goto(SELLER_CENTRAL_URL, wait_until="networkidle")
    await page.wait_for_timeout(3000)

    if "sellercentral.amazon.co.jp" in page.url and "signin" not in page.url and "/ap/" not in page.url:
        logger.info("ログイン済みです（セッション再利用）")
        return True

    logger.warning("ログインが必要です。")
    logger.warning(">>> 開いたブラウザでログインしてください（パスワード または Touch ID）。")
    logger.warning(">>> ログイン完了後、自動的に処理が続行されます（最大5分待機）...")

    try:
        await page.wait_for_url(
            lambda url: "sellercentral.amazon.co.jp" in url and "signin" not in url.lower() and "/ap/" not in url.lower(),
            timeout=300000,
        )
        await page.wait_for_timeout(3000)
        logger.info("ログイン確認OK → 処理を続行します")
        return True
    except PlaywrightTimeout:
        logger.error("5分以内にログインが完了しませんでした。スクリプトを終了します。")
        return False


async def get_orders_for_asin(page, asin: str) -> list:
    """指定ASINの注文IDをorders-v3検索ページから取得する。"""
    search_url = f"{SELLER_CENTRAL_URL}/orders-v3/search?q={asin}&qt=asin"
    logger.info(f"  検索: {search_url}")
    await page.goto(search_url, wait_until="networkidle")
    await page.wait_for_timeout(3000)
    await save_screenshot(page, f"search_{asin}")

    # 注文詳細ページへのリンクhrefからのみ注文IDを抽出（ページテンプレートの誤検出を防ぐ）
    order_ids = set()
    links = await page.query_selector_all("a[href]")
    for link in links:
        href = await link.get_attribute("href") or ""
        if any(kw in href for kw in ["/orders-v3/order/", "orderId=", "orderID=", "order-id="]):
            matches = re.findall(r"\d{3}-\d{7}-\d{7}", href)
            if matches:
                logger.info(f"    注文リンク: {href[:100]}")
                order_ids.update(matches)

    if order_ids:
        return list(order_ids)

    # フォールバック1: 全hrefをスキャン
    for link in links:
        href = await link.get_attribute("href") or ""
        matches = re.findall(r"\d{3}-\d{7}-\d{7}", href)
        order_ids.update(matches)

    if order_ids:
        logger.info(f"  全hrefスキャン結果: {sorted(order_ids)}")
        return list(order_ids)

    # フォールバック2: リンクの表示テキストから注文IDを取得
    for link in links:
        text = (await link.inner_text()).strip()
        matches = re.findall(r"\d{3}-\d{7}-\d{7}", text)
        order_ids.update(matches)

    logger.info(f"  テキストスキャン結果: {sorted(order_ids)}")
    return list(order_ids)


async def get_orders_from_list(page) -> set:
    """
    注文一覧ページから対象ASINに一致する注文IDを取得する。
    ASINが新規注文のASIN検索に反映されるまでのタイムラグを補う。
    """
    list_url = f"{SELLER_CENTRAL_URL}/orders-v3?page=1"
    logger.info(f"注文一覧から新規注文を確認: {list_url}")
    await page.goto(list_url, wait_until="networkidle")
    await page.wait_for_timeout(3000)

    content = await page.content()
    order_ids = set()

    for asin in TARGET_ASINS:
        pos = 0
        while True:
            idx = content.find(asin, pos)
            if idx == -1:
                break
            # ASIN前後500文字以内の注文IDを抽出（同一行内にある）
            context = content[max(0, idx - 500): idx + 500]
            for oid in re.findall(r"\d{3}-\d{7}-\d{7}", context):
                order_ids.add(oid)
                logger.info(f"  一覧から検出: {oid} (ASIN:{asin})")
            pos = idx + 1

    return order_ids


async def send_via_messaging_compose(page, order_id: str) -> bool:
    """
    /messaging/contact へ直接遷移して送信する。
    「注文の詳細を確認する」ラジオ（○→◉）を選択後にメッセージ欄が表示される。
    """
    contact_url = f"{SELLER_CENTRAL_URL}/messaging/contact?orderID={order_id}&marketplaceID={MARKETPLACE_ID}"
    logger.info(f"  メッセージURL: {contact_url}")
    await page.goto(contact_url, wait_until="networkidle")
    await page.wait_for_timeout(2000)

    if "signin" in page.url or "/ap/" in page.url:
        logger.warning(f"  メッセージページへのアクセス失敗（ログイン切れ）")
        return False

    # ラジオボタン選択: 複数の方法で試みる
    radio_selected = False

    # 方法1: labelテキストで検索してクリック
    for radio_text in ["注文の詳細を確認する", "その他"]:
        label = await page.query_selector(f"label:has-text('{radio_text}')")
        if label:
            await label.click()
            await page.wait_for_timeout(2000)
            logger.info(f"  ラジオ選択(label): {radio_text}")
            radio_selected = True
            break

    # 方法2: input[type=radio] を直接クリック
    if not radio_selected:
        first_radio = await page.query_selector("input[type='radio']")
        if first_radio:
            await first_radio.click()
            await page.wait_for_timeout(2000)
            logger.info("  ラジオ選択(input直接)")
            radio_selected = True

    # 方法3: JavaScriptで最初のラジオをクリック
    if not radio_selected:
        await page.evaluate("() => { const r = document.querySelector('input[type=\"radio\"]'); if(r) r.click(); }")
        await page.wait_for_timeout(2000)
        logger.info("  ラジオ選択(JS)")

    # テキストエリアの出現を待つ（最大5秒）
    try:
        textarea = await page.wait_for_selector("textarea", timeout=5000)
        if textarea:
            logger.info("  メッセージ入力欄を検出 → 送信処理へ")
            return await fill_and_send(page, order_id)
    except PlaywrightTimeout:
        pass

    logger.warning(f"  メッセージ入力欄が表示されませんでした: {contact_url}")
    await save_screenshot(page, f"no_textarea_{order_id.replace('-', '_')}")
    return False


async def send_via_order_detail(page, order_id: str) -> bool:
    """注文詳細ページから「購入者に連絡」ボタンを探して送信する。"""
    # 方法A: 注文詳細ページへ直接遷移
    detail_url = f"{SELLER_CENTRAL_URL}/orders-v3/order/{order_id}"
    await page.goto(detail_url, wait_until="networkidle")
    await page.wait_for_timeout(3000)
    await save_screenshot(page, f"detail_{order_id.replace('-', '_')}")

    if await _find_and_click_contact(page, order_id):
        return True

    # 方法B: orders-v3一覧ページで注文行をクリック（コワーク確認済み動作方式）
    list_url = f"{SELLER_CENTRAL_URL}/orders-v3?page=1"
    logger.info(f"  一覧ページから注文を探す: {list_url}")
    await page.goto(list_url, wait_until="networkidle")
    await page.wait_for_timeout(3000)

    order_row = await page.query_selector(f"text={order_id}")
    if order_row:
        await order_row.click()
        await page.wait_for_timeout(2000)
        await save_screenshot(page, f"list_clicked_{order_id.replace('-', '_')}")
        if await _find_and_click_contact(page, order_id):
            return True

    return False


async def _find_and_click_contact(page, order_id: str) -> bool:
    """ページ上の「購入者に連絡」要素を探してクリックし、送信フォームへ進む。"""

    # 1. テキストで直接探す
    for selector in [
        "tr:has-text('購入者に連絡') a",       # 注文詳細ページ: ラベル行内の購入者名リンク
        "div:has-text('購入者に連絡:') a",     # 同上（divレイアウトの場合）
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

    # 3. href に messaging/contact を含むリンクを探す（stale element safe）
    links = await page.query_selector_all("a[href]")
    messaging_urls = []
    for link in links:
        href = await link.get_attribute("href") or ""
        if any(kw in href.lower() for kw in ["messaging", "contact-buyer", "contactbuyer", "contact_buyer", "communication-manager"]):
            text = (await link.inner_text()).strip()
            full_url = href if href.startswith("http") else SELLER_CENTRAL_URL + href
            messaging_urls.append((full_url, text))

    for full_url, text in messaging_urls:
        logger.info(f"  連絡リンク(href): '{text}' -> {full_url}")
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
    if await send_via_messaging_compose(page, order_id):
        return True

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

            # 全対象ASINの注文IDを収集（ASIN検索）
            all_order_ids: set = set()
            for asin in TARGET_ASINS:
                logger.info(f"ASIN {asin} の注文を検索中...")
                order_ids = await get_orders_for_asin(page, asin)
                logger.info(f"  ASIN検索結果: {len(order_ids)}件")
                all_order_ids.update(order_ids)

            # 注文一覧からも収集（新規注文の漏れを防ぐ）
            list_orders = await get_orders_from_list(page)
            new_found = list_orders - all_order_ids
            if new_found:
                logger.info(f"注文一覧から追加検出: {sorted(new_found)}")
            all_order_ids.update(list_orders)
            logger.info(f"処理対象注文ID合計: {len(all_order_ids)}件")

            for order_id in sorted(all_order_ids):
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
