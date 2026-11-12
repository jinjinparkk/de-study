/* 공통 동작: 상단 메뉴, 목차, 코드 복사, 실습 체크, 퀴즈, 진도 저장(localStorage) */
(function () {
  const DAYS = [
    { id: "day1", file: "day1.html", tool: "dbt", title: "큰 그림 — 프로시저에서 dbt로", desc: "ELT·모던 데이터 스택, dbt가 하는 일과 안 하는 일, 첫 프로젝트 실행" },
    { id: "day2", file: "day2.html", tool: "dbt", title: "모델·ref·source·계층", desc: "의존성 그래프(DAG), staging → intermediate → marts, materialization" },
    { id: "day3", file: "day3.html", tool: "dbt", title: "테스트·문서·리니지", desc: "generic·singular 테스트, source freshness, docs, contract, dbt build" },
    { id: "day4", file: "day4.html", tool: "dbt", title: "Jinja·매크로·incremental·snapshot", desc: "MERGE 프로시저 → incremental, SCD2 → snapshot, 패키지" },
    { id: "day5", file: "day5.html", tool: "airflow", title: "Airflow 핵심 개념", desc: "DAG·Task·Operator, 스케줄러, logical date, 백필, 멱등성" },
    { id: "day6", file: "day6.html", tool: "airflow", title: "Airflow로 dbt 돌리기", desc: "BashOperator·Cosmos, 재시도·알림, Asset 스케줄링, 운영 패턴" },
    { id: "day7", file: "day7.html", tool: "spark", title: "Spark 기초와 전체 연결", desc: "드라이버·익스큐터, 지연 실행, 파티션·셔플, Spark vs 웨어하우스" },
  ];
  const EXTRA = [
    { id: "overview", file: "overview.html", title: "dbt 한눈에" },
    { id: "dict", file: "dictionary.html", title: "프로시저↔dbt 사전" },
    { id: "glossary", file: "glossary.html", title: "용어집" },
    { id: "cheatsheet", file: "cheatsheet.html", title: "명령어 모음" },
    { id: "d30", file: "dbt30/index.html", title: "30일 버전 →" },
    { id: "ess", file: "essentials/index.html", title: "필수 정리 →" },
  ];
  window.DE_DAYS = DAYS;

  const body = document.body;
  const page = body.dataset.page || "";
  /* dbt30/ 폴더 안이면 30일 코스 모드: 일차 목록은 assets/dbt30-days.js 의 DBT30_DAYS */
  const in30 = location.pathname.includes("/dbt30/");
  const D30 = window.DBT30_DAYS || [];
  const inDays = location.pathname.includes("/days/");
  /* essentials/ 폴더 = 필수 정리 (본문은 assets/essentials.js 가 그림) */
  const inEss = location.pathname.includes("/essentials/");
  const root = inDays || in30 || inEss ? "../" : "";
  const href = (f) => (f.startsWith("day") ? (inDays ? f : "days/" + f) : root + f);

  const store = {
    get(k, d) { try { const v = localStorage.getItem("de-study:" + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("de-study:" + k, JSON.stringify(v)); } catch (e) {} },
  };
  window.DE_STORE = store;

  /* ---------- 상단 메뉴 ---------- */
  const top = document.createElement("header");
  top.className = "topbar";
  let links;
  if (inEss) {
    links = [`<a href="index.html" class="${page === "ess-home" ? "active" : ""}">목차</a>`]
      .concat([1, 2, 3, 4].map((w) => `<a href="index.html#w${w}">${w}주차</a>`))
      .concat([`<a href="../dbt30/index.html">dbt 30일</a>`, `<a href="../index.html">7일 버전</a>`]);
  } else if (in30) {
    const cur = D30.find((d) => d.id === page);
    links = [`<a href="index.html" class="${page === "d30-home" ? "active" : ""}">30일 홈</a>`]
      .concat([1, 2, 3, 4].map((w) => `<a href="index.html#w${w}">${w}주차</a>`))
      .concat(cur ? [`<a href="${cur.file}" class="active">Day ${cur.n}</a>`] : [])
      .concat([`<a href="modeling.html" class="${page === "d30-modeling" ? "active" : ""}">모델링</a>`, `<a href="../essentials/index.html">필수 정리</a>`])
      .concat([`<a href="../glossary.html">용어집</a>`, `<a href="../cheatsheet.html">명령어 모음</a>`, `<a href="../index.html">← 7일 버전</a>`]);
  } else {
    links = DAYS.map((d, i) => {
      const done = store.get(d.id + ":done", false);
      return `<a href="${href(d.file)}" class="${d.id === page ? "active" : ""} ${done ? "done" : ""}" title="${d.title}">${i + 1}</a>`;
    }).concat(EXTRA.map((e) => `<a href="${href(e.file)}" class="${e.id === page ? "active" : ""}">${e.title}</a>`));
  }
  top.innerHTML = `<div class="topbar-inner"><a class="brand" href="${in30 || inEss ? "index.html" : root + "index.html"}">${in30 ? "DAS · dbt 30일" : inEss ? "DAS · 필수 정리" : "DAS"}</a><nav class="topnav">${links.join("")}</nav></div>`;
  body.prepend(top);

  const main = document.querySelector("main");
  if (!main) return;

  /* ---------- 목차 ---------- */
  const toc = document.querySelector(".toc");
  const heads = [...main.querySelectorAll("h2")];
  heads.forEach((h, i) => { if (!h.id) h.id = "s" + (i + 1); });
  if (toc && heads.length) {
    toc.innerHTML = `<strong>이 페이지</strong><ol>${heads.map((h) => `<li><a href="#${h.id}">${h.textContent}</a></li>`).join("")}</ol><div class="progress-mini"></div>`;
    const tocLinks = [...toc.querySelectorAll("a")];
    const io = new IntersectionObserver((ents) => {
      ents.forEach((en) => {
        if (en.isIntersecting) {
          tocLinks.forEach((a) => a.classList.toggle("on", a.getAttribute("href") === "#" + en.target.id));
        }
      });
    }, { rootMargin: "0px 0px -75% 0px" });
    heads.forEach((h) => io.observe(h));
  }

  /* ---------- 코드 복사 ---------- */
  main.querySelectorAll("pre").forEach((pre) => {
    if (pre.classList.contains("diagram")) return;
    const b = document.createElement("button");
    b.className = "copy-btn";
    b.textContent = "복사";
    b.addEventListener("click", () => {
      const code = pre.querySelector("code") || pre;
      navigator.clipboard.writeText(code.innerText.replace(/\n$/, "")).then(() => {
        b.textContent = "복사됨";
        setTimeout(() => (b.textContent = "복사"), 1200);
      });
    });
    pre.appendChild(b);
  });

  /* ---------- 실습 체크 ---------- */
  const steps = [...main.querySelectorAll(".step")];
  const stepKey = (s, i) => `${page}:step:${s.dataset.id || i}`;
  steps.forEach((s, i) => {
    const bodyDiv = document.createElement("div");
    bodyDiv.className = "step-body";
    while (s.firstChild) bodyDiv.appendChild(s.firstChild);
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.setAttribute("aria-label", "이 단계 완료");
    cb.checked = store.get(stepKey(s, i), false);
    s.classList.toggle("checked", cb.checked);
    cb.addEventListener("change", () => {
      store.set(stepKey(s, i), cb.checked);
      s.classList.toggle("checked", cb.checked);
      updateMini();
    });
    s.appendChild(cb);
    s.appendChild(bodyDiv);
  });

  /* ---------- 퀴즈 ---------- */
  const qs = [...main.querySelectorAll(".q")];
  const quizKey = `${page}:quiz`;
  const saved = store.get(quizKey, {});
  qs.forEach((q, qi) => {
    const ans = parseInt(q.dataset.answer, 10) - 1;
    const ol = q.querySelector(".q-opts");
    const items = [...ol.children];
    const wrap = document.createElement("div");
    wrap.className = "q-opts";
    const buttons = items.map((li, oi) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.innerHTML = `${"①②③④⑤"[oi]} ${li.innerHTML}`;
      btn.addEventListener("click", () => answer(oi));
      wrap.appendChild(btn);
      return btn;
    });
    ol.replaceWith(wrap);
    function answer(oi, silent) {
      buttons.forEach((b, bi) => {
        b.disabled = true;
        if (bi === ans) b.classList.add("right");
        if (bi === oi && oi !== ans) b.classList.add("wrong");
      });
      q.classList.add("answered");
      if (!silent) {
        const s = store.get(quizKey, {});
        s[qi] = oi;
        store.set(quizKey, s);
        updateScore();
        updateMini();
      }
    }
    q._reset = () => {
      buttons.forEach((b) => { b.disabled = false; b.classList.remove("right", "wrong"); });
      q.classList.remove("answered");
    };
    if (saved[qi] !== undefined) answer(saved[qi], true);
  });
  const quizBox = main.querySelector(".quiz");
  let scoreEl;
  if (quizBox && qs.length) {
    scoreEl = document.createElement("div");
    scoreEl.className = "quiz-score";
    const reset = document.createElement("button");
    reset.className = "btn";
    reset.textContent = "퀴즈 다시 풀기";
    reset.style.marginTop = "8px";
    reset.addEventListener("click", () => { store.set(quizKey, {}); qs.forEach((q) => q._reset()); updateScore(); updateMini(); });
    quizBox.appendChild(scoreEl);
    quizBox.appendChild(reset);
    updateScore();
  }
  function updateScore() {
    if (!scoreEl) return;
    const s = store.get(quizKey, {});
    const n = Object.keys(s).length;
    const right = qs.filter((q, i) => s[i] !== undefined && s[i] === parseInt(q.dataset.answer, 10) - 1).length;
    scoreEl.textContent = n ? `${qs.length}문제 중 ${n}문제 풀이 · ${right}개 정답` : `${qs.length}문제`;
  }

  /* ---------- 완료 버튼 + 이전/다음 ---------- */
  const LIST = in30 ? D30 : DAYS;
  const di = LIST.findIndex((d) => d.id === page);
  if (di >= 0) {
    const row = document.createElement("div");
    row.className = "done-row";
    const btn = document.createElement("button");
    const paint = () => {
      const done = store.get(page + ":done", false);
      btn.className = done ? "btn" : "btn primary";
      btn.textContent = done ? "✓ 완료함 (취소하려면 클릭)" : "학습 완료로 표시";
    };
    btn.addEventListener("click", () => {
      store.set(page + ":done", !store.get(page + ":done", false));
      store.set(page + ":doneAt", new Date().toISOString().slice(0, 10));
      paint();
    });
    paint();
    row.appendChild(btn);
    main.appendChild(row);

    const pager = document.createElement("nav");
    pager.className = "pager";
    const prev = LIST[di - 1], next = LIST[di + 1];
    const home = in30 ? "index.html" : "../index.html";
    const ok = (d) => d && (!in30 || d.ready);
    pager.innerHTML =
      (ok(prev) ? `<a href="${prev.file}">← ${di} · ${prev.title}</a>` : `<a href="${home}">← 전체 커리큘럼</a>`) +
      (ok(next) ? `<a href="${next.file}">${di + 2} · ${next.title} →</a>`
        : next ? `<a href="${home}#w${next.week}">Day ${di + 2} · ${next.title} (본문 준비 중) →</a>` : `<a href="${home}">전체 커리큘럼 →</a>`);
    main.appendChild(pager);
  }

  function updateMini() {
    const done = steps.filter((s, i) => store.get(stepKey(s, i), false)).length;
    const qn = Object.keys(store.get(quizKey, {})).length;
    if (di >= 0) store.set(page + ":stat", { steps: done, stepsTotal: steps.length, quiz: qn, quizTotal: qs.length });
    const el = document.querySelector(".progress-mini");
    if (el) el.innerHTML = `실습 ${done}/${steps.length} · 퀴즈 ${qn}/${qs.length}`;
  }
  updateMini();
})();
