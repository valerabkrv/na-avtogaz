#!/usr/bin/env python3
"""
Режет index.html сайта na-avtogaz.ru на блоки T123 для Тильды.

    python3 tilda/split-blocks.py

Что делает:
  * убирает комментарии из CSS (иначе комментарий прилипает к следующему
    селектору и правило умирает) и вешает область видимости .na на каждый селектор;
  * подставляет абсолютные адреса картинок и видео вместо относительных;
  * вырезает мою модалку и меняет кнопки на ссылки #popup:<id> — заявки
    принимает форма Тильды;
  * карточку с формой в контактах меняет на карточку с кнопкой;
  * ограничивает $ и $$ блоками .na, чтобы скрипт не цеплял элементы Тильды;
  * раскладывает всё по файлам blocks/NN-имя.html и собирает страницу-проверку.
"""
import argparse, base64, os, re

SCOPE   = 'na'
SECTIONS = [
    ('ШАПКА',                 'header',   'Шапка и мобильное меню'),
    ('ГЕРОЙ',                 'hero',     'Первый экран с видеообложкой'),
    ('БЕГУЩАЯ СТРОКА',        'marquee',  'Бегущая строка брендов'),
    ('КАЛЬКУЛЯТОР ЭКОНОМИИ',  'calc',     'Калькулятор экономии'),
    ('ЦЕНЫ',                  'price',    'Цены на установку ГБО'),
    ('КАК ПРОХОДИТ УСТАНОВКА','how',      'Как проходит установка (5 шагов)'),
    ('СХЕМА ГБО',             'scheme',   'Из чего состоит ГБО'),
    ('ОБСЛУЖИВАНИЕ И РЕМОНТ', 'service',  'Обслуживание и ремонт'),
    ('ГИБДД',                 'gibdd',    'Оформление в ГИБДД'),
    ('ПОЧЕМУ МЫ',             'why',      'Почему нам доверяют'),
    ('FAQ',                   'faq',      'Вопросы и ответы'),
    ('КОНТАКТЫ',              'contacts', 'Контакты и заявка'),
    ('ПОДВАЛ',                'footer',   'Подвал'),
    ('МОБИЛЬНАЯ ПАНЕЛЬ',      'mbar',     'Мобильная панель и разметка для поиска'),
]
KEEP_AS_IS = ('@keyframes', '@font-face', '@charset', '@import')


def matching_brace(css, j):
    depth = 0
    for k in range(j, len(css)):
        if css[k] == '{': depth += 1
        elif css[k] == '}':
            depth -= 1
            if depth == 0: return k
    return len(css) - 1


def scope_css(css, scope):
    def prefix(sel):
        out = []
        for p in (x.strip() for x in sel.split(',')):
            if not p: continue
            out.append(p if p in (':root', 'html', 'body') else '.%s %s' % (scope, p))
        return ', '.join(out)

    res, i, n = [], 0, len(css)
    while i < n:
        j = css.find('{', i)
        if j == -1:
            res.append(css[i:]); break
        head = css[i:j].strip()
        if head.startswith('@media') or head.startswith('@supports'):
            k = matching_brace(css, j)
            res.append('\n' + head + '{' + scope_css(css[j+1:k], scope) + '}')
            i = k + 1
        elif head.startswith(KEEP_AS_IS):
            k = matching_brace(css, j)
            res.append('\n' + css[i:k+1].strip()); i = k + 1
        else:
            k = css.find('}', j)
            res.append('\n' + prefix(head) + '{' + css[j+1:k].strip() + '}')
            i = k + 1
    return ''.join(res)


def replace_div(body, opener, replacement):
    """Меняет <div ...>...</div> целиком на другой кусок разметки — по месту."""
    i = body.find(opener)
    if i == -1: return body
    depth, j = 0, i
    while j < len(body):
        if body.startswith('<div', j): depth += 1
        elif body.startswith('</div>', j):
            depth -= 1
            if depth == 0:
                j += len('</div>'); break
        j += 1
    return body[:i] + replacement + body[j:]


def cut_div(body, opener):
    """Вырезает <div ...>...</div> целиком по открывающему тегу."""
    i = body.find(opener)
    if i == -1: return body, ''
    depth, j = 0, i
    while j < len(body):
        if body.startswith('<div', j): depth += 1
        elif body.startswith('</div>', j):
            depth -= 1
            if depth == 0:
                j += len('</div>'); break
        j += 1
    return body[:i] + body[j:], body[i:j]


CTA_CARD = '''<div class="form" data-anim="right" style="--d:180ms">
          <h3>Записаться на установку</h3>
          <p>Оставьте номер — перезвоним, уточним марку авто и назовём цену комплекта.</p>
          <ul class="cta-list">
            <li>Осмотр и расчёт — бесплатно, около 30 минут</li>
            <li>Цену фиксируем в договоре до начала работ</li>
            <li>Записываем на ближайшие свободные дни</li>
          </ul>
          <a class="btn btn--main btn--wide" href="#popup:%(popup)s">Оставить заявку</a>
          <p class="form__note">Или звоните — 8 (800) 511-06-88, звонок по России бесплатный.</p>
        </div>'''

CTA_CSS = '''
.%(scope)s, .%(scope)s *{box-sizing:border-box}
.%(scope)s{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  font-size:17px; line-height:1.6; letter-spacing:-.005em; color:var(--ink); background:var(--bg)}
.%(scope)s .cta-list{list-style:none; margin:0 0 26px; padding:0; display:flex; flex-direction:column; gap:12px}
.%(scope)s .cta-list li{position:relative; padding-left:28px; font-size:15.5px; color:var(--ink-2); line-height:1.45}
.%(scope)s .cta-list li::before{content:''; position:absolute; left:0; top:5px; width:18px; height:18px; border-radius:50%%;
  background:var(--green-wash) url("data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%%231B8B05' stroke-width='3.4' stroke-linecap='round' stroke-linejoin='round'%%3E%%3Cpolyline points='20 6 9 17 4 12'/%%3E%%3C/svg%%3E") center/12px no-repeat}
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src', nargs='?', default='index.html')
    ap.add_argument('--outdir', default='tilda/blocks')
    ap.add_argument('--scope', default=SCOPE)
    ap.add_argument('--base', default='', help='адрес папки сайта, например https://valerabkrv.github.io/na-avtogaz/')
    ap.add_argument('--popup', default='zayavka')
    ap.add_argument('--extra-css', default='tilda/popup.css')
    a = ap.parse_args()

    src = open(a.src, encoding='utf-8').read()
    css = re.sub(r'/\*.*?\*/', '', re.search(r'<style>(.*?)</style>', src, re.S).group(1), flags=re.S)
    css = scope_css(css, a.scope) + (CTA_CSS % {'scope': a.scope})
    fonts = ''.join(re.findall(r'<link rel="preconnect"[^>]*>|<link[^>]*fonts\.googleapis[^>]*>', src))
    body = re.search(r'<body>(.*?)</body>', src, re.S).group(1)

    # моя модалка и форма уходят — заявки принимает Тильда
    body, _ = cut_div(body, '<div class="modal" id="modal">')
    body = replace_div(body, '<div class="form" data-anim="right" style="--d:180ms">',
                       CTA_CARD % {'popup': a.popup})
    body = re.sub(r'<button([^>]*?)\sdata-modal\b([^>]*)>(.*?)</button>',
                  lambda m: '<a class="%s" href="#popup:%s">%s</a>' % (
                      (re.search(r'class="([^"]*)"', m.group(1) + m.group(2)) or
                       type('x', (), {'group': lambda self, i: 'btn btn--main'})()).group(1),
                      a.popup, m.group(3)),
                  body, flags=re.S)

    if a.base:
        b = a.base if a.base.endswith('/') else a.base + '/'
        for attr in ('src', 'poster'):
            body = body.replace('%s="img/' % attr, '%s="%simg/' % (attr, b))
            body = body.replace('%s="video/' % attr, '%s="%svideo/' % (attr, b))
    else:
        b = ''

    # Логотип вшиваем прямо в код: это самый заметный элемент страницы, и он не должен
    # зависеть от внешнего хостинга (GitHub Pages у части провайдеров отдаётся с перебоями).
    # Облегчённые версии лежат рядом: tilda/logo-*-inline.png (480 px, ~8 КБ каждая).
    INLINE_IMG = {'img/logo-on-dark.png': 'logo-dark-inline.png',
                  'img/logo-on-light.png': 'logo-light-inline.png'}
    here = os.path.dirname(os.path.abspath(__file__))
    for rel, small in INLINE_IMG.items():
        path = os.path.join(here, small)
        if not os.path.exists(path):
            print('!! нет файла для вшивания:', path)
            continue
        uri = 'data:image/png;base64,' + base64.b64encode(open(path, 'rb').read()).decode()
        before = body
        body = body.replace('src="%s%s"' % (b, rel), 'src="%s"' % uri)
        if before == body:
            print('!! не нашёл в разметке:', b + rel)

    # $ и $$ ищут во всех блоках .na, а не по всей странице Тильды
    body = body.replace(
        "  var $  = function(s,r){return (r||document).querySelector(s)};",
        "  var ROOTS = [].slice.call(document.querySelectorAll('.%s'));\n"
        "  if(!ROOTS.length) ROOTS = [document];\n"
        "  var $  = function(s,r){ if(r) return r.querySelector(s);\n"
        "    for(var i=0;i<ROOTS.length;i++){ var e=ROOTS[i].querySelector(s); if(e) return e } return null };" % a.scope)
    body = body.replace(
        "  var $$ = function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};",
        "  var $$ = function(s,r){ if(r) return Array.prototype.slice.call(r.querySelectorAll(s));\n"
        "    var out=[]; ROOTS.forEach(function(x){ out = out.concat(Array.prototype.slice.call(x.querySelectorAll(s))) }); return out };")

    script = re.search(r'(<script>\n\(function\(\).*?</script>)', body, re.S).group(1)
    body_wo_script = body[:body.find('<script>\n(function()')]

    outdir = a.outdir
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        if f.endswith('.html'): os.remove(os.path.join(outdir, f))

    files = []
    extra = open(a.extra_css, encoding='utf-8').read().strip() if a.extra_css and os.path.exists(a.extra_css) else ''
    files.append(('01-styles.html',
        '<!-- СТИЛИ И ШРИФТЫ сайта na-avtogaz.ru. Этот блок должен быть ПЕРВЫМ на странице.\n'
        '     Сам ничего не выводит. Если его удалить — сайт станет белым текстом на белом фоне. -->\n'
        + fonts + '\n<style>' + css + '\n</style>\n'
        + ('<style>\n/* внешний вид поп-апа с формой Тильды */\n' + extra + '\n</style>\n' if extra else '')))

    marks = {n: body_wo_script.find('<!-- ================= %s =' % n) for n, _, _ in SECTIONS}
    order = [(n, s, t) for n, s, t in SECTIONS if marks[n] != -1]
    for i, (name, slug, title) in enumerate(order):
        start = marks[name]
        end = marks[order[i+1][0]] if i+1 < len(order) else len(body_wo_script)
        chunk = re.sub(r'<!-- ={10,} .+? ={10,} -->\s*', '', body_wo_script[start:end])
        files.append(('%02d-%s.html' % (i+2, slug),
            '<!-- %s | сайт na-avtogaz.ru. Текст и цены можно править прямо здесь. -->\n'
            '<div class="%s">\n%s\n</div>\n' % (title, a.scope, chunk.strip())))

    files.append(('%02d-scripts.html' % (len(order)+2),
        '<!-- СКРИПТЫ сайта na-avtogaz.ru: калькулятор, переключатель цен, аккордеон,\n'
        '     появление секций при прокрутке. Этот блок должен быть ПОСЛЕДНИМ. -->\n' + script + '\n'))

    total = 0
    for fname, content in files:
        open(os.path.join(outdir, fname), 'w', encoding='utf-8').write(content)
        n = len(content.encode('utf-8')); total += n
        print('%-22s %7d байт%s' % (fname, n, '   !! БОЛЬШЕ 100 000' if n > 100000 else ''))
    print('---\nвсего %d блоков, %d байт' % (len(files), total))

    # страница-проверка: имитирует сбросы стилей Тильды
    check = ['<!doctype html><html lang="ru"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<title>Проверка блоков na-avtogaz</title>',
             '<style>*{box-sizing:content-box}body{margin:0}a{color:#ff8562}',
             'h1,h2,h3,h4{font-weight:400;margin:0}ul{list-style:none;padding:0;margin:0}',
             'img{max-width:100%}</style></head><body>']
    for fname, content in files:
        check.append('\n<!-- ===== %s ===== -->\n' % fname + content)
    check.append('</body></html>')
    open(os.path.join(outdir, '..', '_split-check.html'), 'w', encoding='utf-8').write('\n'.join(check))
    print('страница-проверка: %s/_split-check.html' % os.path.dirname(outdir))


if __name__ == '__main__':
    main()
