// Reuse Anki's deck anchors and live count elements so collapse, drag, and
// asynchronous RWKV count updates continue to target the original nodes.
(() => {
    for (const row of document.querySelectorAll("tr.deck[id]")) {
        const cell = row.querySelector(".decktd");
        const name = cell?.querySelector("a.deck");
        const counts = ["new", "learn", "review"].map(kind =>
            document.getElementById("deck-" + row.id + "-" + kind + "-count"));
        if (!name || counts.some(count => !count)) continue;
        const indent = [...cell.childNodes].find(node =>
            node.nodeType === Node.TEXT_NODE && node.textContent.includes("\u00a0"));
        const depth = indent ? Math.floor(indent.textContent.split("\u00a0").length / 6) : 0;
        row.style.setProperty("--indent", Math.min(depth, 6) * 10 + "px");
        if (indent) indent.remove();
        const total = document.createElement("strong");
        const summary = document.createElement("div");
        summary.className = "kioku-counts";
        summary.append(total, " │ ");
        counts.forEach((count, index) => {
            if (index) summary.append(" · ");
            const part = document.createElement("span");
            part.append(count, [" New", " Learning", " To Review"][index]);
            summary.append(part);
        });
        function update() {
            const values = counts.map(count => count.textContent.trim());
            total.textContent = (values.every(value => /^\d+$/.test(value))
                ? values.reduce((sum, value) => sum + Number(value), 0) : "…") + " Total";
        }
        const observer = new MutationObserver(update);
        counts.forEach(count => observer.observe(count, {childList:true, subtree:true, characterData:true}));
        update();
        const limit = document.getElementById("deck-" + row.id + "-review-limit");
        if (limit) summary.append(limit);
        const disclosure = cell.querySelector("a.collapse");
        if (disclosure) {
            const collapsed = disclosure.textContent.trim() === "+";
            disclosure.textContent = collapsed ? "›" : "⌄";
            disclosure.setAttribute("aria-expanded", String(!collapsed));
            disclosure.setAttribute("aria-label", (collapsed ? "Expand " : "Collapse ") + name.textContent);
        }
        cell.append(summary);
        row.closest("table").classList.add("kioku-decks");
    }
})();
