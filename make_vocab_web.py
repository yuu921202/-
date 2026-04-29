from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "vocabulary_unique.csv"
OUT_PATH = ROOT / "vocab_quiz.html"


def load_vocab() -> list[dict[str, str]]:
    if not CSV_PATH.exists():
        raise SystemExit("找不到 vocabulary_unique.csv，請先執行：python ppt_vocab_quiz.py extract")

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    return [
        {
            "term": row.get("term", "").strip(),
            "meaning": (row.get("short_definition") or row.get("definition") or "").strip(),
            "definition": row.get("definition", "").strip(),
            "source": row.get("source_file", "").strip(),
            "slide": row.get("slide_no", "").strip(),
        }
        for row in rows
        if row.get("term") and (row.get("short_definition") or row.get("definition"))
    ]


def render_html(entries: list[dict[str, str]]) -> str:
    data = json.dumps(entries, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>單字小考</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #19202a;
      --muted: #64717d;
      --paper: #f7f8f5;
      --panel: #ffffff;
      --line: #d9dfdd;
      --nav: #213044;
      --nav-soft: #2f425d;
      --accent: #087d82;
      --accent-ink: #05565a;
      --warm: #b86120;
      --good: #167447;
      --bad: #b43b2a;
      --focus: #f3c85f;
      --shadow: 0 18px 45px rgba(27, 36, 48, .10);
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        linear-gradient(90deg, rgba(8,125,130,.10) 0 16px, transparent 16px),
        linear-gradient(180deg, #fbfbf8, var(--paper));
      font-family: "Segoe UI", "Noto Sans TC", "Microsoft JhengHei", Arial, sans-serif;
      letter-spacing: 0;
    }}

    button, input, select {{
      font: inherit;
    }}

    button {{
      cursor: pointer;
    }}

    .app {{
      min-height: 100vh;
      display: grid;
      grid-template-columns: 292px minmax(0, 1fr);
    }}

    .sidebar {{
      color: white;
      background: var(--nav);
      padding: 24px 20px;
      display: flex;
      flex-direction: column;
      gap: 22px;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .mark {{
      width: 46px;
      height: 46px;
      flex: 0 0 auto;
      border: 1px solid rgba(255,255,255,.28);
      border-radius: 8px;
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 4px;
      padding: 6px;
      background: rgba(255,255,255,.08);
    }}

    .mark span {{
      border-radius: 4px;
      background: #f3c85f;
    }}

    .mark span:nth-child(2) {{ background: #66c2b8; }}
    .mark span:nth-child(3) {{ background: #ee8b62; }}
    .mark span:nth-child(4) {{ background: #f6f1df; }}

    h1 {{
      margin: 0;
      font-size: 1.42rem;
      line-height: 1.15;
      font-weight: 800;
    }}

    .brand small {{
      display: block;
      color: rgba(255,255,255,.72);
      margin-top: 4px;
      font-size: .82rem;
    }}

    .nav-tabs {{
      display: grid;
      gap: 8px;
    }}

    .nav-tabs button,
    .primary,
    .ghost {{
      border: 0;
      border-radius: 8px;
      min-height: 42px;
      padding: 10px 12px;
      transition: transform .16s ease, background .16s ease, border-color .16s ease;
    }}

    .nav-tabs button {{
      text-align: left;
      color: rgba(255,255,255,.78);
      background: transparent;
    }}

    .nav-tabs button.active {{
      color: white;
      background: var(--nav-soft);
    }}

    .side-box {{
      border-top: 1px solid rgba(255,255,255,.18);
      padding-top: 18px;
      display: grid;
      gap: 12px;
    }}

    .side-box label {{
      color: rgba(255,255,255,.72);
      font-size: .85rem;
      display: grid;
      gap: 6px;
    }}

    .side-box select {{
      width: 100%;
      border: 1px solid rgba(255,255,255,.18);
      border-radius: 8px;
      color: white;
      background: #172538;
      padding: 9px 10px;
    }}

    .stat-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }}

    .stat {{
      min-height: 70px;
      border: 1px solid rgba(255,255,255,.14);
      border-radius: 8px;
      padding: 10px;
      background: rgba(255,255,255,.06);
    }}

    .stat strong {{
      display: block;
      font-size: 1.35rem;
    }}

    .stat span {{
      color: rgba(255,255,255,.65);
      font-size: .78rem;
    }}

    main {{
      min-width: 0;
      padding: 24px;
      display: grid;
      align-content: start;
      gap: 18px;
    }}

    .toolbar {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 14px;
    }}

    .toolbar h2 {{
      margin: 0;
      font-size: 1.2rem;
    }}

    .toolbar p {{
      margin: 4px 0 0;
      color: var(--muted);
      font-size: .92rem;
    }}

    .segmented {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}

    .segmented button {{
      border: 1px solid var(--line);
      border-radius: 8px;
      min-height: 38px;
      padding: 8px 12px;
      color: var(--ink);
      background: var(--panel);
    }}

    .segmented button.active {{
      color: white;
      border-color: var(--accent);
      background: var(--accent);
    }}

    .quiz-panel,
    .list-panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }}

    .quiz-panel {{
      min-height: 520px;
      padding: 22px;
      display: grid;
      grid-template-rows: auto auto minmax(210px, auto) auto;
      gap: 18px;
    }}

    .progress-row {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      color: var(--muted);
      font-size: .9rem;
    }}

    .meter {{
      height: 9px;
      background: #e9eeeb;
      border-radius: 999px;
      overflow: hidden;
    }}

    .meter span {{
      display: block;
      width: 0%;
      height: 100%;
      background: linear-gradient(90deg, var(--accent), var(--warm));
      transition: width .22s ease;
    }}

    .question {{
      display: grid;
      gap: 10px;
      align-content: center;
      min-height: 148px;
      padding: 18px;
      border-left: 5px solid var(--accent);
      background: #f9fbfa;
      border-radius: 8px;
    }}

    .question-label {{
      color: var(--muted);
      font-size: .88rem;
    }}

    .question-text {{
      margin: 0;
      font-size: clamp(1.45rem, 2vw, 2.05rem);
      line-height: 1.35;
      font-weight: 800;
      overflow-wrap: anywhere;
    }}

    .source {{
      min-height: 22px;
      color: var(--muted);
      font-size: .86rem;
    }}

    .options {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      align-content: start;
    }}

    .option {{
      width: 100%;
      min-height: 74px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      color: var(--ink);
      background: white;
      text-align: left;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }}

    .option:hover,
    .option:focus-visible,
    .primary:hover,
    .ghost:hover,
    .segmented button:hover {{
      transform: translateY(-1px);
    }}

    .option.correct {{
      border-color: rgba(22,116,71,.45);
      background: #edf8f1;
    }}

    .option.wrong {{
      border-color: rgba(180,59,42,.42);
      background: #fff0ec;
    }}

    .feedback {{
      min-height: 28px;
      font-weight: 700;
      color: var(--muted);
    }}

    .feedback.good {{ color: var(--good); }}
    .feedback.bad {{ color: var(--bad); }}

    .actions {{
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      flex-wrap: wrap;
    }}

    .primary {{
      color: white;
      background: var(--accent);
      padding-inline: 18px;
    }}

    .ghost {{
      color: var(--accent-ink);
      background: #eaf6f5;
      padding-inline: 16px;
    }}

    .typing {{
      display: grid;
      gap: 12px;
    }}

    .typing input {{
      width: 100%;
      min-height: 52px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px 14px;
      font-size: 1.05rem;
    }}

    .typing .answer {{
      min-height: 44px;
      color: var(--muted);
      overflow-wrap: anywhere;
    }}

    .summary {{
      display: grid;
      gap: 14px;
      align-content: center;
      min-height: 360px;
      text-align: center;
    }}

    .summary strong {{
      display: block;
      font-size: clamp(2.4rem, 7vw, 5rem);
      line-height: 1;
    }}

    .miss-list {{
      max-height: 220px;
      overflow: auto;
      text-align: left;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      background: #fbfbfa;
    }}

    .miss-list div {{
      padding: 7px 0;
      border-bottom: 1px solid #edf0ee;
    }}

    .miss-list div:last-child {{
      border-bottom: 0;
    }}

    .list-panel {{
      padding: 18px;
      display: grid;
      gap: 14px;
    }}

    .list-tools {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 180px;
      gap: 12px;
    }}

    .list-tools input,
    .list-tools select {{
      width: 100%;
      min-height: 42px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 9px 11px;
      background: white;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }}

    th, td {{
      padding: 10px 8px;
      border-bottom: 1px solid #edf0ee;
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }}

    th {{
      color: var(--muted);
      font-size: .82rem;
      font-weight: 700;
    }}

    th:nth-child(1), td:nth-child(1) {{ width: 28%; }}
    th:nth-child(3), td:nth-child(3) {{ width: 16%; }}

    .hidden {{ display: none !important; }}

    @media (max-width: 900px) {{
      .app {{
        grid-template-columns: 1fr;
      }}

      .sidebar {{
        position: static;
        padding: 18px;
      }}

      .stat-grid {{
        grid-template-columns: repeat(4, 1fr);
      }}

      main {{
        padding: 18px;
      }}

      .toolbar,
      .list-tools {{
        grid-template-columns: 1fr;
      }}
    }}

    @media (max-width: 620px) {{
      .options {{
        grid-template-columns: 1fr;
      }}

      .quiz-panel {{
        padding: 16px;
      }}

      .stat-grid {{
        grid-template-columns: 1fr 1fr;
      }}

      th:nth-child(3), td:nth-child(3) {{
        display: none;
      }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <div class="mark" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
        <div>
          <h1>單字小考</h1>
          <small id="datasetLabel">讀取中</small>
        </div>
      </div>

      <nav class="nav-tabs" aria-label="主選單">
        <button id="quizTab" class="active" type="button">小考</button>
        <button id="listTab" type="button">單字表</button>
      </nav>

      <section class="side-box" aria-label="小考設定">
        <label>
          題型
          <select id="modeSelect">
            <option value="meaning-to-term">看中文選英文</option>
            <option value="term-to-meaning">看英文選中文</option>
            <option value="typing">中翻英打字</option>
          </select>
        </label>
        <label>
          範圍
          <select id="chapterSelect"></select>
        </label>
        <label>
          題數
          <select id="countSelect">
            <option value="10">10 題</option>
            <option value="20" selected>20 題</option>
            <option value="30">30 題</option>
            <option value="50">50 題</option>
            <option value="all">全部</option>
          </select>
        </label>
        <button class="primary" id="startBtn" type="button">開始新小考</button>
      </section>

      <section class="side-box" aria-label="成績">
        <div class="stat-grid">
          <div class="stat"><strong id="scoreStat">0</strong><span>答對</span></div>
          <div class="stat"><strong id="doneStat">0</strong><span>已答</span></div>
          <div class="stat"><strong id="rateStat">0%</strong><span>正確率</span></div>
          <div class="stat"><strong id="leftStat">0</strong><span>剩餘</span></div>
        </div>
      </section>
    </aside>

    <main>
      <section id="quizView">
        <div class="toolbar">
          <div>
            <h2 id="quizTitle">看中文選英文</h2>
            <p id="quizSubtitle">Ch1 到 Ch7，共 {len(entries)} 個單字/片語</p>
          </div>
          <div class="segmented" role="group" aria-label="題型切換">
            <button data-mode="meaning-to-term" class="active" type="button">中 → 英</button>
            <button data-mode="term-to-meaning" type="button">英 → 中</button>
            <button data-mode="typing" type="button">打字</button>
          </div>
        </div>

        <div class="quiz-panel">
          <div class="progress-row">
            <div class="meter" aria-hidden="true"><span id="meterFill"></span></div>
            <span id="progressText">0 / 0</span>
          </div>

          <div class="question">
            <div class="question-label" id="questionLabel">題目</div>
            <p class="question-text" id="questionText"></p>
            <div class="source" id="sourceText"></div>
          </div>

          <div id="choiceArea" class="options"></div>
          <div id="typingArea" class="typing hidden">
            <input id="typingInput" type="text" autocomplete="off" spellcheck="false" placeholder="輸入英文單字或片語">
            <div class="answer" id="typingAnswer"></div>
          </div>

          <div>
            <div class="feedback" id="feedback"></div>
            <div class="actions">
              <button class="ghost" id="showAnswerBtn" type="button">顯示答案</button>
              <button class="primary" id="nextBtn" type="button">下一題</button>
            </div>
          </div>
        </div>
      </section>

      <section id="listView" class="list-panel hidden">
        <div class="toolbar">
          <div>
            <h2>單字表</h2>
            <p id="listCount"></p>
          </div>
        </div>
        <div class="list-tools">
          <input id="searchInput" type="search" placeholder="搜尋英文、中文、來源">
          <select id="listChapterSelect"></select>
        </div>
        <div style="overflow:auto">
          <table>
            <thead>
              <tr><th>單字</th><th>意思</th><th>章節</th></tr>
            </thead>
            <tbody id="wordRows"></tbody>
          </table>
        </div>
      </section>
    </main>
  </div>

  <script id="vocab-data" type="application/json">{data}</script>
  <script>
    const DATA = JSON.parse(document.getElementById('vocab-data').textContent);
    const $ = (selector) => document.querySelector(selector);
    const $$ = (selector) => Array.from(document.querySelectorAll(selector));

    const els = {{
      datasetLabel: $('#datasetLabel'),
      quizTab: $('#quizTab'),
      listTab: $('#listTab'),
      quizView: $('#quizView'),
      listView: $('#listView'),
      modeSelect: $('#modeSelect'),
      chapterSelect: $('#chapterSelect'),
      listChapterSelect: $('#listChapterSelect'),
      countSelect: $('#countSelect'),
      startBtn: $('#startBtn'),
      quizTitle: $('#quizTitle'),
      quizSubtitle: $('#quizSubtitle'),
      questionLabel: $('#questionLabel'),
      questionText: $('#questionText'),
      sourceText: $('#sourceText'),
      choiceArea: $('#choiceArea'),
      typingArea: $('#typingArea'),
      typingInput: $('#typingInput'),
      typingAnswer: $('#typingAnswer'),
      feedback: $('#feedback'),
      showAnswerBtn: $('#showAnswerBtn'),
      nextBtn: $('#nextBtn'),
      meterFill: $('#meterFill'),
      progressText: $('#progressText'),
      scoreStat: $('#scoreStat'),
      doneStat: $('#doneStat'),
      rateStat: $('#rateStat'),
      leftStat: $('#leftStat'),
      searchInput: $('#searchInput'),
      listCount: $('#listCount'),
      wordRows: $('#wordRows'),
    }};

    const state = {{
      mode: 'meaning-to-term',
      chapter: 'all',
      questions: [],
      options: [],
      index: 0,
      score: 0,
      answered: false,
      wrong: [],
      current: null,
    }};

    function escapeHtml(value) {{
      return String(value || '').replace(/[&<>"']/g, char => ({{
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      }}[char]));
    }}

    function chapterOf(entry) {{
      const text = entry.source || '';
      const match = text.match(/ch\\s*(\\d+)/i);
      return match ? `Ch${{match[1]}}` : '其他';
    }}

    function sourceLabel(entry) {{
      const source = (entry.source || '').split(/[\\\\/]/).pop() || 'PPT';
      return `${{chapterOf(entry)}} · Slide ${{entry.slide || '?'}} · ${{source}}`;
    }}

    function shuffle(items) {{
      const copy = [...items];
      for (let i = copy.length - 1; i > 0; i--) {{
        const j = Math.floor(Math.random() * (i + 1));
        [copy[i], copy[j]] = [copy[j], copy[i]];
      }}
      return copy;
    }}

    function normalizeAnswer(text) {{
      return String(text || '').trim().toLowerCase().replace(/\\s+/g, ' ');
    }}

    function currentPool() {{
      return DATA.filter(entry => state.chapter === 'all' || chapterOf(entry) === state.chapter);
    }}

    function optionText(entry) {{
      return state.mode === 'term-to-meaning' ? entry.meaning : entry.term;
    }}

    function questionText(entry) {{
      if (state.mode === 'term-to-meaning') return entry.term;
      return entry.meaning;
    }}

    function answerText(entry) {{
      if (state.mode === 'term-to-meaning') return entry.meaning;
      return entry.term;
    }}

    function modeTitle(mode = state.mode) {{
      return {{
        'meaning-to-term': '看中文選英文',
        'term-to-meaning': '看英文選中文',
        'typing': '中翻英打字',
      }}[mode];
    }}

    function buildChapterOptions() {{
      const chapters = [...new Set(DATA.map(chapterOf))].sort((a, b) => {{
        const an = Number(a.replace(/\\D/g, '')) || 999;
        const bn = Number(b.replace(/\\D/g, '')) || 999;
        return an - bn || a.localeCompare(b);
      }});

      const options = ['<option value="all">全部章節</option>', ...chapters.map(ch => `<option value="${{ch}}">${{ch}}</option>`)].join('');
      els.chapterSelect.innerHTML = options;
      els.listChapterSelect.innerHTML = options;
    }}

    function startQuiz() {{
      state.mode = els.modeSelect.value;
      state.chapter = els.chapterSelect.value;
      const pool = currentPool();
      const wanted = els.countSelect.value === 'all' ? pool.length : Number(els.countSelect.value);
      state.questions = shuffle(pool).slice(0, Math.min(wanted, pool.length));
      state.index = 0;
      state.score = 0;
      state.answered = false;
      state.wrong = [];
      setActiveModeButton();
      renderQuiz();
    }}

    function buildChoiceQuestion(entry) {{
      const pool = currentPool().filter(item => item.term !== entry.term && optionText(item));
      const options = shuffle([entry, ...shuffle(pool).slice(0, 3)]);
      return options;
    }}

    function renderQuiz() {{
      els.quizTitle.textContent = modeTitle();
      els.quizSubtitle.textContent = `${{state.chapter === 'all' ? '全部章節' : state.chapter}} · ${{currentPool().length}} 個單字/片語`;
      renderStats();

      if (!state.questions.length) {{
        els.questionText.textContent = '這個範圍沒有可用單字';
        els.choiceArea.innerHTML = '';
        els.typingArea.classList.add('hidden');
        els.sourceText.textContent = '';
        els.feedback.textContent = '';
        return;
      }}

      if (state.index >= state.questions.length) {{
        renderSummary();
        return;
      }}

      const entry = state.questions[state.index];
      state.current = entry;
      state.answered = false;
      els.feedback.textContent = '';
      els.feedback.className = 'feedback';
      els.typingAnswer.textContent = '';
      els.typingInput.value = '';
      els.nextBtn.textContent = '下一題';
      els.showAnswerBtn.classList.toggle('hidden', state.mode !== 'typing');
      els.questionLabel.textContent = state.mode === 'term-to-meaning' ? '英文單字' : '中文意思';
      els.questionText.textContent = questionText(entry);
      els.sourceText.textContent = sourceLabel(entry);
      updateProgress();

      if (state.mode === 'typing') {{
        els.choiceArea.classList.add('hidden');
        els.typingArea.classList.remove('hidden');
        window.setTimeout(() => els.typingInput.focus(), 50);
        return;
      }}

      els.choiceArea.classList.remove('hidden');
      els.typingArea.classList.add('hidden');
      const options = buildChoiceQuestion(entry);
      state.options = options;
      els.choiceArea.innerHTML = options.map((option, index) => `
        <button class="option" type="button" data-option-index="${{index}}">
          <strong>${{index + 1}}.</strong> ${{escapeHtml(optionText(option))}}
        </button>
      `).join('');
    }}

    function answerChoice(optionIndex) {{
      if (state.answered || !state.current) return;
      const picked = state.options[Number(optionIndex)];
      if (!picked) return;
      state.answered = true;
      const correct = picked.term === state.current.term;
      if (correct) {{
        state.score += 1;
        els.feedback.textContent = '答對';
        els.feedback.className = 'feedback good';
      }} else {{
        state.wrong.push(state.current);
        els.feedback.textContent = `答錯，答案是：${{answerText(state.current)}}`;
        els.feedback.className = 'feedback bad';
      }}

      $$('.option').forEach(button => {{
        const option = state.options[Number(button.dataset.optionIndex)];
        const isCorrect = option && option.term === state.current.term;
        const isPicked = option && option.term === picked.term;
        button.disabled = true;
        if (isCorrect) button.classList.add('correct');
        if (isPicked && !isCorrect) button.classList.add('wrong');
      }});
      renderStats();
    }}

    function answerTyping(showOnly = false) {{
      if (!state.current) return;
      const expected = normalizeAnswer(state.current.term);
      const typed = normalizeAnswer(els.typingInput.value);
      const correct = typed === expected;

      if (showOnly) {{
        els.typingAnswer.textContent = `答案：${{state.current.term}}`;
        return;
      }}

      if (state.answered) return;
      state.answered = true;
      if (correct) {{
        state.score += 1;
        els.feedback.textContent = '答對';
        els.feedback.className = 'feedback good';
      }} else {{
        state.wrong.push(state.current);
        els.feedback.textContent = '答錯';
        els.feedback.className = 'feedback bad';
      }}
      els.typingAnswer.textContent = `答案：${{state.current.term}}`;
      renderStats();
    }}

    function nextQuestion() {{
      if (state.index >= state.questions.length) {{
        startQuiz();
        return;
      }}
      if (state.mode === 'typing' && !state.answered) {{
        answerTyping(false);
        return;
      }}
      if (!state.answered && state.mode !== 'typing') {{
        els.feedback.textContent = '先選一個答案';
        return;
      }}
      state.index += 1;
      renderQuiz();
    }}

    function renderSummary() {{
      const total = state.questions.length;
      const rate = total ? Math.round((state.score / total) * 100) : 0;
      updateProgress(true);
      els.sourceText.textContent = '';
      els.choiceArea.classList.remove('hidden');
      els.typingArea.classList.add('hidden');
      els.showAnswerBtn.classList.add('hidden');
      els.feedback.textContent = '';
      els.questionLabel.textContent = '完成';
      els.questionText.textContent = `${{state.score}} / ${{total}}`;
      els.choiceArea.innerHTML = `
        <div class="summary" style="grid-column: 1 / -1">
          <div><strong>${{rate}}%</strong><span>正確率</span></div>
          ${{state.wrong.length ? `<div class="miss-list">${{state.wrong.map(item => `<div><b>${{escapeHtml(item.term)}}</b>：${{escapeHtml(item.meaning)}}</div>`).join('')}}</div>` : '<p>這輪全部答對。</p>'}}
        </div>
      `;
      els.nextBtn.textContent = '再考一次';
      renderStats();
    }}

    function updateProgress(done = false) {{
      const total = state.questions.length || 0;
      const doneCount = done ? total : Math.min(state.index, total);
      const percent = total ? Math.round((doneCount / total) * 100) : 0;
      els.meterFill.style.width = `${{percent}}%`;
      els.progressText.textContent = `${{doneCount}} / ${{total}}`;
    }}

    function renderStats() {{
      const total = state.questions.length;
      const done = Math.min(state.index + (state.answered ? 1 : 0), total);
      const left = Math.max(total - done, 0);
      const rate = done ? Math.round((state.score / done) * 100) : 0;
      els.scoreStat.textContent = state.score;
      els.doneStat.textContent = done;
      els.rateStat.textContent = `${{rate}}%`;
      els.leftStat.textContent = left;
    }}

    function setMode(mode) {{
      state.mode = mode;
      els.modeSelect.value = mode;
      setActiveModeButton();
      startQuiz();
    }}

    function setActiveModeButton() {{
      $$('.segmented button').forEach(button => {{
        button.classList.toggle('active', button.dataset.mode === els.modeSelect.value);
      }});
    }}

    function showView(view) {{
      const isQuiz = view === 'quiz';
      els.quizView.classList.toggle('hidden', !isQuiz);
      els.listView.classList.toggle('hidden', isQuiz);
      els.quizTab.classList.toggle('active', isQuiz);
      els.listTab.classList.toggle('active', !isQuiz);
      if (!isQuiz) renderList();
    }}

    function renderList() {{
      const keyword = normalizeAnswer(els.searchInput.value);
      const chapter = els.listChapterSelect.value;
      const rows = DATA.filter(entry => {{
        const inChapter = chapter === 'all' || chapterOf(entry) === chapter;
        const haystack = normalizeAnswer(`${{entry.term}} ${{entry.meaning}} ${{entry.source}}`);
        return inChapter && (!keyword || haystack.includes(keyword));
      }});
      els.listCount.textContent = `${{rows.length}} 個單字/片語`;
      els.wordRows.innerHTML = rows.slice(0, 500).map(entry => `
        <tr>
          <td><strong>${{escapeHtml(entry.term)}}</strong></td>
          <td>${{escapeHtml(entry.meaning)}}</td>
          <td>${{escapeHtml(chapterOf(entry))}} · ${{escapeHtml(entry.slide || '?')}}</td>
        </tr>
      `).join('');
    }}

    els.datasetLabel.textContent = `${{DATA.length}} 個單字/片語`;
    buildChapterOptions();
    startQuiz();

    els.startBtn.addEventListener('click', startQuiz);
    els.modeSelect.addEventListener('change', () => setMode(els.modeSelect.value));
    els.chapterSelect.addEventListener('change', startQuiz);
    els.countSelect.addEventListener('change', startQuiz);
    els.nextBtn.addEventListener('click', nextQuestion);
    els.showAnswerBtn.addEventListener('click', () => answerTyping(true));
    els.choiceArea.addEventListener('click', event => {{
      const button = event.target.closest('.option');
      if (button) answerChoice(button.dataset.optionIndex);
    }});
    els.typingInput.addEventListener('keydown', event => {{
      if (event.key === 'Enter') nextQuestion();
    }});
    els.quizTab.addEventListener('click', () => showView('quiz'));
    els.listTab.addEventListener('click', () => showView('list'));
    els.searchInput.addEventListener('input', renderList);
    els.listChapterSelect.addEventListener('change', renderList);
    $$('.segmented button').forEach(button => {{
      button.addEventListener('click', () => setMode(button.dataset.mode));
    }});
    document.addEventListener('keydown', event => {{
      if (state.mode === 'typing') return;
      if (/^[1-4]$/.test(event.key)) {{
        const option = $$('.option')[Number(event.key) - 1];
        if (option) answerChoice(option.dataset.optionIndex);
      }}
      if (event.key === 'Enter') nextQuestion();
    }});
  </script>
</body>
</html>
"""


def main() -> int:
    entries = load_vocab()
    OUT_PATH.write_text(render_html(entries), encoding="utf-8")
    print(f"已產生 {OUT_PATH}")
    print(f"單字數：{len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
