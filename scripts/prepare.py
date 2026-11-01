"""Split the captured reference into editable static assets; apply the Russian content."""
import json
import re
from pathlib import Path
from urllib.request import urlopen

root = Path(__file__).resolve().parent.parent
reference = root / 'research/reference.html'
if not reference.exists():
    reference.parent.mkdir(exist_ok=True)
    with urlopen('https://pristine-zone-6q93xmk.shipstatic.com/', timeout=30) as response:
        reference.write_bytes(response.read())
html = (root / 'research/reference.html').read_text(encoding='utf-8-sig')
style = re.search(r'<style>(.*?)</style>', html, re.S).group(1)
script = re.search(r'<script>(.*?)</script>', html, re.S).group(1)
data = json.loads(re.search(r'const DATA=(.*?);\n', script).group(1))
names = dict(line.split('=', 1) for line in (root / 'src/pet-names-ru.txt').read_text(encoding='utf-8').splitlines() if '=' in line)
def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
missing = []
for pet in data['pets']:
    pet['nameEn'] = pet['name']
    translated = names.get(slug(pet['name']))
    if translated:
        pet['nameRu'] = translated
    else:
        missing.append(pet['name'])
for monster in data['monsters']:
    monster['nameEn'] = monster['name']
    monster['nameRu'] = names.get(slug(monster['name']), monster['name'])
for zone, name, short in zip(data['meta']['zones'], ['Бертрон', 'Альтгард', 'Нижняя Решанта'], ['Б', 'А', 'Р']):
    zone.update(nameRu=name, shortRu=short)
public = root / 'public'
public.mkdir(exist_ok=True)
(public / 'data.js').write_text('const DATA=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
(public / 'names-ru.js').write_text("for(const p of DATA.pets)p.name=p.nameRu||p.name;\nfor(const m of DATA.monsters)m.name=m.nameRu||m.name;\nfor(const z of DATA.meta.zones){z.name=z.nameRu;z.short=z.shortRu;}\n", encoding='utf-8')
(public / 'styles.css').write_text(style + '\n' + (root / 'src/overrides.css').read_text(encoding='utf-8'), encoding='utf-8')
script = script[script.index('const ZONES='):]
start, end = script.index('const GUIDE='), script.index('let state=')
script = script[:start] + script[end:]
script = script.replace("const STORAGE='aion2-pet-atlas-v3';", "const STORAGE='aion2-progress-ru-v1';")
start, end = script.index('try{\n  let saved='), script.index('let view=')
script = script[:start] + "try{const raw=localStorage.getItem(STORAGE);if(raw)Object.assign(state,normalizeProgress(JSON.parse(raw),DATA,GUIDE,CHECKLIST));}catch{queueMicrotask(()=>toast('Сохранение не прочитано. Исходные данные оставлены в браузере; восстановите прогресс из JSON.'));}\n" + script[end:]
script = script.replace("function save(){localStorage.setItem(STORAGE,JSON.stringify({target:state.target,ranks:state.ranks,guide:state.guide,checklist:state.checklist}));}", "function save(){try{localStorage.setItem(STORAGE,JSON.stringify({target:state.target,ranks:state.ranks,guide:state.guide,checklist:state.checklist}));}catch{toast('Не удалось сохранить прогресс. Экспортируйте JSON, чтобы не потерять изменения.');}}")
start, end = script.index('function importProgress('), script.index('function toast(')
script = script[:start] + "function importProgress(obj){const next=normalizeProgress(obj,DATA,GUIDE,CHECKLIST);Object.assign(state,next);save();render();toast('Прогресс импортирован.');}\n" + script[end:]
script = script.replace("if(!f)return;importProgress", "if(!f)return;if(f.size>1024*1024)throw Error('Файл больше 1 МБ. Выберите экспорт прогресса.');importProgress")
script = script.replace("return p.name.toLowerCase().includes(q)||monsterNames(p).some(n=>n.toLowerCase().includes(q));", "return p.name.toLowerCase().includes(q)||p.nameEn.toLowerCase().includes(q)||categoryName(p.category).toLowerCase().includes(q)||monsterNames(p).some(n=>n.toLowerCase().includes(q))||p.sources.flat().some(i=>monsterByIndex[i].nameEn.toLowerCase().includes(q));")
script = script.replace('slug(p.name)===k', 'slug(p.nameEn)===k')
script = script.replace('esc(p.category)', 'esc(categoryName(p.category))')
script = script.replace("e=>{if(e.key==='Enter'||e.key===' '){", "e=>{if(e.target.closest('.rank'))return;if(e.key==='Enter'||e.key===' '){")
script = script.replace('aria-label="${done?', 'aria-pressed="${done}" aria-label="${done?')
script = script.replace("el.className='toast';", "el.className='toast';el.setAttribute('role','status');")
script = script.replace("const pets=state.page==='pets'", "history.replaceState(null,'','#'+state.page);document.querySelectorAll('.languageSwitch a').forEach(a=>{const url=new URL(a.href);url.hash=state.page;a.href=url.href;});const pets=state.page==='pets'")
script = script.replace("switchPage('guide');requestAnimationFrame", "switchPage(location.hash.slice(1));requestAnimationFrame")
script = script.replace("${esc(p.name)}</div><div class=\"badges\">", "${esc(p.name)}</div><div class=\"petEnglish\">${esc(p.nameEn)}</div><div class=\"badges\">")
script = script.replace("const PREV_STORAGE='aion2-pet-atlas-v2';\nconst OLD_STORAGE='aion2-verteron-pet-atlas-v1';\n", '')
script = script.replace("const $=", "const categoryName=c=>({Cogni:'Разумные',Fera:'Дикие',Natura:'Вириды',Varian:'Метаморфы',Special:'Особые'})[c]||c;\nconst $=")
script = script.replace("${section==='events'?'Scheduled / opportunistic':section}", "${({daily:'Каждый день',weekly:'Каждую неделю',events:'По расписанию'})[section]||''}")
script = script.replace("${p.spawnCounts[zi].toLocaleString()} ${ZONES[zi].name} spawn${p.spawnCounts[zi]===1?'':'s'}", "${ZONES[zi].name}: ${p.spawnCounts[zi].toLocaleString('ru-RU')} точек")
script = script.replace("${p.spawnCounts[state.zone].toLocaleString()} verified ${z.name} spawns", "${z.name}: ${p.spawnCounts[state.zone].toLocaleString('ru-RU')} точек")
script = script.replace("${DATA.pets.length} Global pets · ${DATA.meta.spawnCount.toLocaleString()} verified field-source spawns · ${DATA.meta.priorityCount} field pets with no Verteron source.", "${DATA.pets.length} питомцев · ${DATA.meta.spawnCount.toLocaleString('ru-RU')} точек появления · ${DATA.meta.priorityCount} питомца вне Бертрона")
script = script.replace("${activeSpawnIndexes.length.toLocaleString()} pins · ${activePets} missing pets", "${activeSpawnIndexes.length.toLocaleString('ru-RU')} точек · ${activePets} несобранных питомцев")
script = script.replace("${p.label.replace('Phase ','P')}", "${p.label.replace('Этап ','Э')}")
replacements = json.loads((root / 'src/ui-ru.json').read_text(encoding='utf-8'))
for old, new in sorted(replacements.items(), key=lambda p: -len(p[0])):
    script = script.replace(old, new)
html = re.sub(r'<style>.*?</style>', '<link rel="stylesheet" href="styles.css">', html, flags=re.S)
html = re.sub(r'<script>.*?</script>', '<script src="data.js"></script>\n<script src="content.js"></script>\n<script src="progress.js"></script>\n<script src="app.js"></script>', html, flags=re.S)
html = html.replace('lang="en"', 'lang="ru"')
html = html.replace('<script src="content.js">', '<script src="names-ru.js"></script>\n<script src="content.js">')
html = html.replace('<option>Cogni</option><option>Fera</option><option>Natura</option><option>Varian</option><option>Special</option>', '<option value="Cogni">Разумные</option><option value="Fera">Дикие</option><option value="Natura">Вириды</option><option value="Varian">Метаморфы</option><option value="Special">Особые</option>')
for old, new in sorted(replacements.items(), key=lambda p: -len(p[0])):
    html = html.replace(old, new)
for en, ru in [('Cogni','Разумные'),('Fera','Дикие'),('Natura','Вириды'),('Varian','Метаморфы'),('Special','Особые')]:
    html = html.replace('</i>'+en+'</span>', '</i>'+ru+'</span>')
html = html.replace('id="search" type=', 'id="search" aria-label="Поиск питомца или монстра" type=').replace('id="category"', 'id="category" aria-label="Тип питомца"').replace('id="availability"', 'id="availability" aria-label="Доступность питомца"')
html = html.replace('<div class="toptools">', '<div class="toptools"><span class="localStatus">● Сохранение в браузере</span><div class="languageSwitch" aria-label="Язык"><a href="./" lang="ru" aria-current="page">RU</a><a href="en/" lang="en">EN</a></div>')
html = html.replace('V = Verteron · A = Altgard · R = Reshanta', 'Б = Бертрон · А = Альтгард · Р = Решанта')
html = html.replace('</footer>', '<span>Названия: <a href="https://wikily.gg/ru/aion-2/pets" target="_blank" rel="noopener">Wikily</a></span></footer>')
(public / 'index.html').write_text(html, encoding='utf-8')
(public / 'app.js').write_text(script, encoding='utf-8')
for name in ['content.js', 'progress.js']:
    (public / name).write_text((root / 'src' / name).read_text(encoding='utf-8'), encoding='utf-8')
en = public / 'en'
en.mkdir(exist_ok=True)
original = (root / 'research/reference.html').read_text(encoding='utf-8-sig')
en_script = re.search(r'<script>(.*?)</script>', original, re.S).group(1)
en_script = en_script[en_script.index('const ZONES='):]
en_script = en_script.replace("const STORAGE='aion2-pet-atlas-v3';", "const STORAGE='aion2-progress-ru-v1';")
en_script = en_script.replace("const PREV_STORAGE='aion2-pet-atlas-v2';\nconst OLD_STORAGE='aion2-verteron-pet-atlas-v1';\n", '')
start, end = en_script.index('try{\n  let saved='), en_script.index('let view=')
en_script = en_script[:start] + "try{const raw=localStorage.getItem(STORAGE);if(raw)Object.assign(state,normalizeProgress(JSON.parse(raw),DATA,GUIDE,CHECKLIST));}catch{queueMicrotask(()=>toast('Could not read saved progress. The original data remains in this browser; restore a JSON backup.'));}\n" + en_script[end:]
en_script = en_script.replace("function save(){localStorage.setItem(STORAGE,JSON.stringify({target:state.target,ranks:state.ranks,guide:state.guide,checklist:state.checklist}));}", "function save(){try{localStorage.setItem(STORAGE,JSON.stringify({target:state.target,ranks:state.ranks,guide:state.guide,checklist:state.checklist}));}catch{toast('Could not save progress. Export a JSON backup to keep your changes.');}}")
start, end = en_script.index('function importProgress('), en_script.index('function toast(')
en_script = en_script[:start] + "function importProgress(obj){const next=normalizeProgress(obj,DATA,GUIDE,CHECKLIST);Object.assign(state,next);save();render();toast('Progress imported.');}\n" + en_script[end:]
en_script = en_script.replace("if(!f)return;importProgress", "if(!f)return;if(f.size>1024*1024)throw Error('File exceeds 1 MB. Choose a progress export.');importProgress")
en_script = en_script.replace("p.name.toLowerCase().includes(q)", "(p.name.toLowerCase().includes(q)||(p.nameRu||'').toLowerCase().includes(q))")
en_script = en_script.replace("e=>{if(e.key==='Enter'||e.key===' '){", "e=>{if(e.target.closest('.rank'))return;if(e.key==='Enter'||e.key===' '){")
en_script = en_script.replace('aria-label="${done?', 'aria-pressed="${done}" aria-label="${done?')
en_script = en_script.replace("el.className='toast';", "el.className='toast';el.setAttribute('role','status');")
en_script = en_script.replace("const pets=state.page==='pets'", "history.replaceState(null,'','#'+state.page);document.querySelectorAll('.languageSwitch a').forEach(a=>{const url=new URL(a.href);url.hash=state.page;a.href=url.href;});const pets=state.page==='pets'")
en_script = en_script.replace("switchPage('guide');requestAnimationFrame", "switchPage(location.hash.slice(1));requestAnimationFrame")
en_html = re.sub(r'<style>.*?</style>', '<link rel="stylesheet" href="../styles.css">', original, flags=re.S)
en_html = re.sub(r'<script>.*?</script>', '<script src="../data.js"></script>\n<script src="../progress.js"></script>\n<script src="app.js"></script>', en_html, flags=re.S)
en_html = en_html.replace('<div class="toptools">', '<div class="toptools"><span class="localStatus">● Saved in this browser</span><div class="languageSwitch" aria-label="Language"><a href="../" lang="ru">RU</a><a href="./" lang="en" aria-current="page">EN</a></div>')
en_html = en_html.replace('id="search" type=', 'id="search" aria-label="Search pet or source monster" type=').replace('id="category"', 'id="category" aria-label="Pet type"').replace('id="availability"', 'id="availability" aria-label="Pet availability"')
en_html = en_html.replace('</footer>', '<span>Russian names: <a href="https://wikily.gg/ru/aion-2/pets" target="_blank" rel="noopener">Wikily</a></span></footer>')
(en / 'index.html').write_text(en_html, encoding='utf-8')
(en / 'app.js').write_text(en_script, encoding='utf-8')
print('Prepared Russian app. Unmatched pets:', missing)
