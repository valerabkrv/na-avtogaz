#!/usr/bin/env python3
"""
Собирает отдельную страницу 404 из основного index.html.

    python3 make-404.py

Берёт из index.html стили, шапку с мобильным меню, подвал и скрипты —
поэтому 404 всегда выглядит как основной сайт. Меняет только середину.
На выходе:
    404.html                     — страница для GitHub Pages (он сам её отдаёт на битых адресах)
    tilda/blocks-404/01..05.html — те же куски блоками T123 для отдельной страницы в Тильде
"""
import os, re

SRC = "index.html"
src = open(SRC, encoding="utf-8").read()

fonts  = "".join(re.findall(r'<link rel="preconnect"[^>]*>|<link[^>]*fonts\.googleapis[^>]*>', src))
style  = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
body   = re.search(r"<body>(.*?)</body>", src, re.S).group(1)

def section(name, nxt):
    a = body.index("<!-- ================= %s =" % name)
    b = body.index("<!-- ================= %s =" % nxt)
    return re.sub(r"<!-- ={10,} .+? ={10,} -->\s*", "", body[a:b]).strip()

header = section("ШАПКА", "ГЕРОЙ")                 # шапка + мобильное меню
footer = section("ПОДВАЛ", "МОБИЛЬНАЯ ПАНЕЛЬ")
script = re.search(r"(<script>\n\(function\(\).*?</script>)", body, re.S).group(1)

# на 404 ссылки меню должны вести на главную, а не на несуществующие якоря
def to_home(chunk):
    return re.sub(r'href="#(?!popup:)([a-z]+)"', r'href="/#\1"', chunk).replace('href="#top"', 'href="/"')

header_404, footer_404 = to_home(header), to_home(footer)

EXTRA_CSS = """
/* ============ страница 404 ============ */
.err{min-height:calc(100svh - 78px); display:flex; align-items:center; padding:clamp(96px,14vh,150px) 0 clamp(56px,8vh,96px)}
.err__in{max-width:760px; margin:0 auto; text-align:center}
.err__code{font-family:'Manrope',sans-serif; font-weight:800; font-size:clamp(96px,20vw,210px); line-height:.86;
  letter-spacing:-.06em; background:linear-gradient(96deg,var(--green-lite),var(--green) 55%,#2FE36A);
  -webkit-background-clip:text; background-clip:text; color:transparent}
.err h1{margin:22px 0 0; font-size:clamp(28px,4.4vw,52px)}
.err__descr{margin-top:20px; font-size:clamp(16px,1.5vw,20px); color:#A9B4BF; line-height:1.55}
.err__acts{margin-top:34px; display:flex; flex-wrap:wrap; gap:14px; justify-content:center}
.err__links{margin-top:clamp(34px,5vh,54px); padding-top:30px; border-top:1px solid rgba(255,255,255,.12)}
.err__links small{display:block; font-size:13px; letter-spacing:.14em; text-transform:uppercase; color:#8D99A5; margin-bottom:16px}
.err__chips{display:flex; flex-wrap:wrap; gap:10px; justify-content:center}
.err__chips a{padding:10px 18px; border-radius:100px; border:1px solid rgba(255,255,255,.18);
  background:rgba(255,255,255,.05); font-size:15px; color:#D7DEE5; transition:.35s var(--ease)}
.err__chips a:hover{background:rgba(53,196,10,.16); border-color:var(--green); color:#fff}
.err__help{margin-top:26px; font-size:14.5px; color:#8D99A5}
.err__help a{color:var(--green-lite); font-weight:600}
@media (max-width:620px){ .err__acts .btn{width:100%} }
"""

MAIN = """<!-- ================= 404 ================= -->
<section class="sec sec--dark err" id="err">
  <div class="wrap err__in">
    <div class="err__code" data-anim="zoom">404</div>
    <h1 data-anim style="--d:120ms">Такой страницы нет</h1>
    <p class="err__descr" data-anim style="--d:200ms">Возможно, в адресе опечатка или страница переехала. Всё про установку ГБО — на главной: цены, калькулятор экономии, этапы работ и заявка на расчёт.</p>
    <div class="err__acts" data-anim style="--d:280ms">
      <a class="btn btn--main" href="/">Вернуться на главную</a>
      <a class="btn btn--ghost" href="tel:+78005110688">8 (800) 511-06-88</a>
    </div>
    <div class="err__links" data-anim="up" style="--d:360ms">
      <small>Популярные разделы</small>
      <div class="err__chips">
        <a href="/#calc">Калькулятор экономии</a>
        <a href="/#price">Цены</a>
        <a href="/#how">Как ставим</a>
        <a href="/#service">Обслуживание</a>
        <a href="/#gibdd">ГИБДД</a>
        <a href="/#contacts">Контакты</a>
      </div>
      <p class="err__help">Если сайт открывается с ошибкой или страница не грузится — напишите нам в <a href="https://wa.me/79226969219" target="_blank" rel="noopener">WhatsApp</a>, ответим и подскажем.</p>
    </div>
  </div>
</section>
"""

page = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Страница не найдена — na-avtogaz.ru</title>
<meta name="description" content="Такой страницы на сайте na-avtogaz.ru нет. Вернитесь на главную: установка ГБО в Челябинске под ключ, от 35 000 ₽.">
<meta name="robots" content="noindex, follow">
<meta name="theme-color" content="#0B0E11">
<link rel="icon" type="image/png" href="img/favicon-512.png">
<link rel="apple-touch-icon" href="img/favicon-180.png">
<meta name="format-detection" content="telephone=no">
{fonts}
<style>{style}
{EXTRA_CSS}</style>
</head>
<body>

{header_404}

{MAIN}
{footer_404}

{script}
</body>
</html>
"""
open("404.html", "w", encoding="utf-8").write(page)
print("404.html — %d байт" % os.path.getsize("404.html"))

# ---- блоки для отдельной страницы в Тильде ----
import importlib.util
spec = importlib.util.spec_from_file_location("sb", os.path.join("tilda", "split-blocks.py"))
sb = importlib.util.module_from_spec(spec); spec.loader.exec_module(sb)

SCOPE = "na"
BASE = "https://valerabkrv.github.io/na-avtogaz/"
outdir = os.path.join("tilda", "blocks-404")
os.makedirs(outdir, exist_ok=True)
for f in os.listdir(outdir):
    if f.endswith(".html"): os.remove(os.path.join(outdir, f))

css = re.sub(r"/\*.*?\*/", "", style + EXTRA_CSS, flags=re.S)
css = sb.scope_css(css, SCOPE) + (sb.CTA_CSS % {"scope": SCOPE})
extra = open(os.path.join("tilda", "popup.css"), encoding="utf-8").read().strip()

def prep(chunk):
    out = chunk
    for attr in ("src", "poster"):
        out = out.replace('%s="img/' % attr, '%s="%simg/' % (attr, BASE))
        out = out.replace('%s="video/' % attr, '%s="%svideo/' % (attr, BASE))
    for rel, small in (("img/logo-on-dark.png", "logo-dark-inline.png"),
                       ("img/logo-on-light.png", "logo-light-inline.png")):
        path = os.path.join("tilda", small)
        if os.path.exists(path):
            import base64
            uri = "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()
            out = out.replace('src="%s%s"' % (BASE, rel), 'src="%s"' % uri)
    return out

blocks = [
    ("01-styles.html",
     "<!-- СТИЛИ И ШРИФТЫ страницы 404. Этот блок должен быть ПЕРВЫМ. Ничего не выводит. -->\n"
     + fonts + "\n<style>" + css + "\n</style>\n<style>\n/* внешний вид блоков Тильды */\n" + extra + "\n</style>\n"),
    ("02-header.html", "<!-- Шапка и мобильное меню | страница 404. Ссылки ведут на главную. -->\n"
     + '<div class="%s">\n%s\n</div>\n' % (SCOPE, prep(header_404))),
    ("03-main.html",   "<!-- Экран «Страница не найдена» | текст и ссылки можно править прямо здесь. -->\n"
     + '<div class="%s">\n%s\n</div>\n' % (SCOPE, re.sub(r"<!-- ={10,} .+? ={10,} -->\s*", "", MAIN).strip())),
    ("04-footer.html", "<!-- Подвал с реквизитами | страница 404. -->\n"
     + '<div class="%s">\n%s\n</div>\n' % (SCOPE, prep(footer_404))),
    ("05-scripts.html","<!-- СКРИПТЫ: неоновый фон и появление блоков. Должен быть ПОСЛЕДНИМ. -->\n" + script + "\n"),
]
total = 0
for name, content in blocks:
    open(os.path.join(outdir, name), "w", encoding="utf-8").write(content)
    n = len(content.encode("utf-8")); total += n
    print("%-18s %7d байт%s" % (name, n, "   !! БОЛЬШЕ 100 000" if n > 100000 else ""))
print("---\nвсего %d блоков, %d байт" % (len(blocks), total))
