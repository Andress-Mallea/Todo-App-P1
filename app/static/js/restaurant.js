const TOKEN_KEY = "access_token";
const TABLES = ["category", "product", "customer", "dining_table",
                "customer_order", "order_line", "promotion", "promotion_product"];
const PER_PAGE = 50;
const $ = (id) => document.getElementById(id);

let current = TABLES[0];
let page = 1;

function getToken() {
    return sessionStorage.getItem(TOKEN_KEY);
}

function hasAccess() {
    try {
        const part = getToken().split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
        const p = JSON.parse(atob(part));
        return p.exp * 1000 > Date.now()
            && Array.isArray(p.permissions)
            && p.permissions.includes("get:restaurant");
    } catch {
        return false;
    }
}

function show(message) {
    const box = $("message");
    box.textContent = message;
    box.className = "flash flash-error";
    box.hidden = !message;
}

function buildTabs() {
    $("tabs").replaceChildren(...TABLES.map((name) => {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = name;
        b.className = "btn btn-small " + (name === current ? "btn-primary" : "btn-light");
        b.addEventListener("click", () => { current = name; page = 1; buildTabs(); load(); });
        return b;
    }));
}

function renderTable({ columns, rows, total, page: p, pages }) {
    $("table-title").textContent = `content.${current}`;
    $("table-info").textContent = `${total} registros — página ${p} de ${pages}`;

    const head = document.createElement("tr");
    columns.forEach((c) => {
        const th = document.createElement("th");
        th.textContent = c;
        head.append(th);
    });
    $("data-head").replaceChildren(head);

    $("data-body").replaceChildren(...rows.map((row) => {
        const tr = document.createElement("tr");
        row.forEach((value) => {
            const td = document.createElement("td");
            td.textContent = value === null ? "—" : String(value);
            tr.append(td);
        });
        return tr;
    }));

    $("prev").disabled = p <= 1;
    $("next").disabled = p >= pages;
}

async function load() {
    show("");
    const res = await fetch(`/api/restaurant/${current}?page=${page}&per_page=${PER_PAGE}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
    });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401) {
        sessionStorage.removeItem(TOKEN_KEY);
        return init();
    }
    if (!res.ok) return show(data.message || `HTTP ${res.status}`);
    renderTable(data);
}

function init() {
    const ok = hasAccess();
    $("need-login").hidden = ok;
    $("restaurant-view").hidden = !ok;
    if (ok) { buildTabs(); load(); }
}

$("prev").addEventListener("click", () => { page -= 1; load(); });
$("next").addEventListener("click", () => { page += 1; load(); });

init();