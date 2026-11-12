/* 필수 정리(essentials) 전용: 작은 마크다운 렌더러 + 목차/상세 페이지 동작.
   콘텐츠는 essentials/curriculum.json 과 essentials/days/dayNN.md 에 있습니다.
   외부 라이브러리를 쓰지 않으므로 지원 문법은 essentials/README.md 에 정리된 것만입니다. */
(function () {
  const S = window.DE_STORE || {
    get(k, d) { try { const v = localStorage.getItem("de-study:" + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("de-study:" + k, JSON.stringify(v)); } catch (e) {} },
  };
  const pad = (n) => String(n).padStart(2, "0");
  const doneKey = (n) => `ess-day${pad(n)}:done`;
  const isDone = (n) => !!S.get(doneKey(n), false);
  const setDone = (n, v) => S.set(doneKey(n), !!v);

  /* ---------- 마크다운 → HTML ---------- */
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  function inline(s) {
    const codes = [];
    s = s.replace(/`([^`]+)`/g, (_, c) => { codes.push(c); return "\u0000" + (codes.length - 1) + "\u0000"; });
    s = esc(s)
      .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
      .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2">$1</a>');
    return s.replace(/\u0000(\d+)\u0000/g, (_, i) => `<code>${esc(codes[+i])}</code>`);
  }
  const slug = (t, used) => {
    let base = "s-" + t.replace(/[^\w가-힣]+/g, "-").replace(/^-|-$/g, "").toLowerCase();
    let id = base, k = 2;
    while (used.has(id)) id = base + "-" + k++;
    used.add(id);
    return id;
  };
  function md(src, used = new Set()) {
    const lines = src.replace(/\r\n?/g, "\n").split("\n");
    const out = [];
    let i = 0;
    const isBlockStart = (l) => /^(#{1,4} |```|:::|> |- |\* |\d+\. |\|)/.test(l) || l.trim() === "" || /^---+$/.test(l.trim());
    while (i < lines.length) {
      const l = lines[i];
      if (l.trim() === "") { i++; continue; }
      let m;
      if (/^---+$/.test(l.trim())) { out.push("<hr>"); i++; continue; }
      if ((m = l.match(/^(#{1,4}) (.*)$/))) {
        const lv = Math.max(2, m[1].length); // # 도 h2 로 (h1 은 페이지 제목)
        const text = m[2].trim();
        out.push(`<h${lv} id="${slug(text, used)}">${inline(text)}</h${lv}>`);
        i++; continue;
      }
      if ((m = l.match(/^```(\w*)\s*(.*)$/))) {
        const lang = m[1], label = m[2];
        const buf = [];
        i++;
        while (i < lines.length && !/^```\s*$/.test(lines[i])) buf.push(lines[i++]);
        i++;
        const diagram = lang === "text" || lang === "erd" || lang === "diagram";
        const file = label ? ` data-file="${esc(label)}"` : lang && !diagram ? ` data-file="${esc(lang.toUpperCase())}"` : "";
        out.push(`<pre${diagram ? ' class="diagram"' : ""}${file}><code>${esc(buf.join("\n"))}</code></pre>`);
        continue;
      }
      if ((m = l.match(/^:::(\w+)\s*(.*)$/))) {
        const kind = m[1], title = m[2].trim();
        const buf = [];
        i++;
        while (i < lines.length && !/^:::\s*$/.test(lines[i])) buf.push(lines[i++]);
        i++;
        const inner = md(buf.join("\n"), used);
        if (kind === "answer") {
          out.push(`<details class="hint answer"><summary>${inline(title || "모범 답안 보기")}</summary>${inner}</details>`);
        } else {
          const cls = { tip: "tip", warn: "warn", summary: "summary", analogy: "analogy", proc: "proc", note: "" }[kind] ?? "";
          out.push(`<div class="box ${cls}">${title ? `<span class="box-title">${inline(title)}</span>` : ""}${inner}</div>`);
        }
        continue;
      }
      if (l.startsWith("> ")) {
        const buf = [];
        while (i < lines.length && lines[i].startsWith(">")) buf.push(lines[i++].replace(/^> ?/, ""));
        out.push(`<div class="box">${md(buf.join("\n"), used)}</div>`);
        continue;
      }
      if (l.startsWith("|")) {
        const rows = [];
        while (i < lines.length && lines[i].startsWith("|")) rows.push(lines[i++]);
        const cells = (r) => r.trim().replace(/^\||\|$/g, "").split(/(?<!\\)\|/).map((c) => inline(c.trim().replace(/\\\|/g, "|")));
        const hasHead = rows.length > 1 && /^\|?\s*:?-{2,}/.test(rows[1]);
        let h = '<div class="table-wrap"><table>';
        if (hasHead) h += "<tr>" + cells(rows[0]).map((c) => `<th>${c}</th>`).join("") + "</tr>";
        rows.slice(hasHead ? 2 : 0).forEach((r) => { h += "<tr>" + cells(r).map((c) => `<td>${c}</td>`).join("") + "</tr>"; });
        out.push(h + "</table></div>");
        continue;
      }
      if (/^(- |\* )/.test(l) || /^\d+\. /.test(l)) {
        const ordered = /^\d+\. /.test(l);
        const re = ordered ? /^\d+\. / : /^(- |\* )/;
        const items = [];
        while (i < lines.length && (re.test(lines[i]) || (/^ {2,}\S/.test(lines[i]) && items.length))) {
          if (re.test(lines[i])) items.push(lines[i].replace(re, ""));
          else items[items.length - 1] += " " + lines[i].trim();
          i++;
        }
        const tag = ordered ? "ol" : "ul";
        out.push(`<${tag}>${items.map((t) => `<li>${inline(t)}</li>`).join("")}</${tag}>`);
        continue;
      }
      const buf = [];
      while (i < lines.length && !isBlockStart(lines[i])) buf.push(lines[i++]);
      if (!buf.length) buf.push(lines[i++]);
      out.push(`<p>${inline(buf.join(" "))}</p>`);
    }
    return out.join("\n");
  }
  window.ESS_MD = md;

  const load = (url) => fetch(url, { cache: "no-cache" }).then((r) => { if (!r.ok) throw new Error(url + " " + r.status); return r; });
  const fail = (el, e) => {
    el.innerHTML = `<div class="box warn"><span class="box-title">불러오지 못했습니다</span>${esc(String(e.message || e))}<br>파일을 직접 열었다면(file://) 로컬 서버로 여세요: <code>python -m http.server 8004</code></div>`;
  };

  /* ---------- 목차 페이지 ---------- */
  function renderIndex(root) {
    load("curriculum.json").then((r) => r.json()).then((C) => {
      const paint = () => {
        const n = C.days.filter((d) => isDone(d.day)).length;
        document.getElementById("ess-bar").style.width = Math.round((n / C.days.length) * 100) + "%";
        document.getElementById("ess-num").textContent = `${n} / ${C.days.length} 완료 · ${Math.round((n / C.days.length) * 100)}%`;
      };
      root.innerHTML = C.weeks.map((w) => `
        <h2 id="w${w.week}">${esc(w.title)}</h2>
        <div class="ess-grid">${C.days.filter((d) => d.week === w.week).map((d) => `
          <div class="ess-card${isDone(d.day) ? " done" : ""}" data-day="${d.day}">
            <a href="day.html?d=${d.day}" class="ess-link">
              <span class="ess-num">Day ${d.day}</span>
              <span class="ess-title">${esc(d.title)}</span>
              <span class="ess-sum">${esc(d.summary)}</span>
            </a>
            <label class="ess-check"><input type="checkbox" ${isDone(d.day) ? "checked" : ""}> 완료</label>
          </div>`).join("")}
        </div>`).join("");
      root.querySelectorAll(".ess-card").forEach((card) => {
        const n = +card.dataset.day;
        card.querySelector("input").addEventListener("change", (e) => {
          setDone(n, e.target.checked);
          card.classList.toggle("done", e.target.checked);
          paint();
        });
      });
      paint();
      if (location.hash) { const t = document.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView(); }
    }).catch((e) => fail(root, e));
  }

  /* ---------- 상세 페이지 ---------- */
  function renderDay(root) {
    const n = parseInt(new URLSearchParams(location.search).get("d"), 10) || 1;
    Promise.all([load("curriculum.json").then((r) => r.json()), load(`days/day${pad(n)}.md`).then((r) => r.text())])
      .then(([C, text]) => {
        const d = C.days.find((x) => x.day === n);
        if (!d) throw new Error(`Day ${n} 없음`);
        const wk = C.weeks.find((w) => w.week === d.week);
        document.title = `Day ${n} · ${d.title} — 필수 정리`;
        const prev = C.days.find((x) => x.day === n - 1), next = C.days.find((x) => x.day === n + 1);
        root.innerHTML = `
          <div class="eyebrow">필수 정리 · Day ${n} · ${esc(wk ? wk.title : "")}</div>
          <h1>${esc(d.title)}</h1>
          <p class="lead">${esc(d.summary)}</p>
          ${md(text.replace(/\r\n?/g, "\n").replace(/^﻿?# .*\n/, ""))}
          <div class="done-row"><label class="ess-check big"><input type="checkbox" id="ess-done" ${isDone(n) ? "checked" : ""}> 이 Day 학습 완료</label></div>
          <nav class="pager">
            ${prev ? `<a href="day.html?d=${prev.day}">← Day ${prev.day} · ${esc(prev.title)}</a>` : "<span></span>"}
            <a href="index.html#w${d.week}">목차로</a>
            ${next ? `<a href="day.html?d=${next.day}">Day ${next.day} · ${esc(next.title)} →</a>` : "<span></span>"}
          </nav>`;
        document.getElementById("ess-done").addEventListener("change", (e) => setDone(n, e.target.checked));
        // 목차(오른쪽 위가 아니라 왼쪽 aside) 와 코드 복사 버튼
        const toc = document.querySelector(".toc");
        const heads = [...root.querySelectorAll("h2")];
        if (toc) toc.innerHTML = `<strong>Day ${n}</strong><ol>${heads.map((h) => `<li><a href="#${h.id}">${h.textContent}</a></li>`).join("")}</ol><p style="margin-top:14px"><a href="index.html">← 필수 정리 목차</a></p>`;
        root.querySelectorAll("pre").forEach((pre) => {
          if (pre.classList.contains("diagram")) return;
          const b = document.createElement("button");
          b.className = "copy-btn"; b.textContent = "복사";
          b.addEventListener("click", () => navigator.clipboard.writeText(pre.querySelector("code").innerText).then(() => { b.textContent = "복사됨"; setTimeout(() => (b.textContent = "복사"), 1200); }));
          pre.appendChild(b);
        });
        if (location.hash) { const t = document.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView(); }
      }).catch((e) => fail(root, e));
  }

  const idx = document.getElementById("ess-index");
  if (idx) renderIndex(idx);
  const day = document.getElementById("ess-day");
  if (day) renderDay(day);
})();
