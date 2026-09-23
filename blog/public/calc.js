// 買取せどり 利益計算ツール（記事内の .calc ブロックで動作）
(function () {
  document.querySelectorAll('[data-calc="kaitori"]').forEach(function (root) {
    var get = function (name) {
      var el = root.querySelector('[name="' + name + '"]');
      var v = parseFloat(el && el.value);
      return isFinite(v) ? v : 0;
    };
    var yen = function (n) {
      return (n < 0 ? '−' : '') + Math.abs(Math.round(n)).toLocaleString('ja-JP') + '円';
    };
    var out = root.querySelector('.calc-result');

    function update() {
      var buy = get('buy');
      var cost = get('cost');
      var pointRate = get('point') / 100;
      var shipBox = get('ship');
      var qty = Math.max(1, Math.floor(get('qty')));
      var other = get('other');
      var minProfit = get('minProfit');
      var minRate = get('minRate') / 100;

      var shipPer = shipBox / qty;
      var profit = buy - cost - shipPer - other;
      var rate = cost > 0 ? profit / cost : 0;
      var points = cost * pointRate;
      var ok = cost > 0 && buy > 0 && profit >= minProfit && rate >= minRate;

      out.classList.toggle('ng', !ok);
      if (!(cost > 0 && buy > 0)) {
        out.innerHTML = '買取価格と仕入れ価格を入力してください。';
        return;
      }
      out.innerHTML =
        '<div class="verdict">' + (ok ? '仕入れ基準クリア' : '見送り（基準未達）') + '</div>' +
        '1点あたり送料：' + yen(shipPer) + '<br>' +
        '利益（現金ベース）：<strong>' + yen(profit) + '</strong>／利益率：<strong>' + (rate * 100).toFixed(1) + '%</strong><br>' +
        'ポイント還元（別枠）：+' + yen(points) + '（ポイント込み利益 ' + yen(profit + points) + '）<br>' +
        '買取価格が10%下がった場合：' + yen(profit - buy * 0.1);
    }

    root.addEventListener('input', update);
    update();
  });
})();
