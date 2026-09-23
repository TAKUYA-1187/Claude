<?php
/**
 * Plugin Name: Sedori Note Kit
 * Description: 「せどり実務ノート」の記事を WordPress で表示するための部品（要点ボックス・利益計算ツール・note 案内・PR表記の見た目）と、GitHub からの自動投稿で使う同期用メタ情報。
 * Version: 1.0.0
 * Requires at least: 6.0
 * Requires PHP: 7.4
 * License: GPL-2.0-or-later
 * Text Domain: sedori-note-kit
 */

if (!defined('ABSPATH')) {
    exit;
}

const SEDORI_NOTE_KIT_VERSION = '1.0.0';

/**
 * 記事の見た目（要点ボックス・計算ツール・note 案内・PR表記）。
 * テーマ（SWELL・Cocoon など）の見出しや表のデザインは上書きしない。
 */
add_action('wp_enqueue_scripts', function () {
    if (!is_singular()) {
        return;
    }
    $base = plugin_dir_url(__FILE__) . 'assets/';
    wp_enqueue_style('sedori-note-kit', $base . 'sedori-note-kit.css', [], SEDORI_NOTE_KIT_VERSION);

    $post = get_post();
    if ($post && strpos($post->post_content, 'data-calc="kaitori"') !== false) {
        wp_enqueue_script('sedori-note-kit-calc', $base . 'calc.js', [], SEDORI_NOTE_KIT_VERSION, true);
    }
});

/**
 * GitHub Actions からの同期（wordpress/publish_wp.py）が、変更のない記事を上書きしないための目印。
 * 記事の元になった Markdown のハッシュを保存する。編集できるユーザーだけが読み書きできる。
 */
add_action('init', function () {
    foreach (['post', 'page'] as $type) {
        register_post_meta($type, 'sedori_source_hash', [
            'type' => 'string',
            'single' => true,
            'show_in_rest' => true,
            'auth_callback' => function () {
                return current_user_can('edit_posts');
            },
        ]);
    }
});

/**
 * 計算ツールの入力欄（input）は、投稿者が「unfiltered_html」を持たないと保存時に消える。
 * 管理者以外のユーザーで同期する場合に備え、計算ツールで使う要素と属性だけ許可する。
 */
add_filter('wp_kses_allowed_html', function ($tags, $context) {
    if ($context !== 'post') {
        return $tags;
    }
    $tags['input'] = [
        'name' => true,
        'type' => true,
        'inputmode' => true,
        'value' => true,
        'min' => true,
        'step' => true,
        'checked' => true,
        'disabled' => true,
    ];
    $tags['details'] = ['open' => true, 'class' => true];
    $tags['summary'] = ['class' => true];
    foreach (['div', 'aside', 'p', 'ul', 'li', 'a', 'label', 'h4'] as $tag) {
        if (!isset($tags[$tag])) {
            $tags[$tag] = [];
        }
        $tags[$tag]['class'] = true;
        $tags[$tag]['data-calc'] = true;
        $tags[$tag]['aria-live'] = true;
    }
    return $tags;
}, 10, 2);
