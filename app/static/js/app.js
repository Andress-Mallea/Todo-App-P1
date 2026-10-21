const TOKEN_KEY = "access_token";
const STATE_KEY = "oauth_state";
const $ = (id) => document.getElementById(id);

// --- Token ---
function getToken() {
    return sessionStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
}

function payload() {
    const token = getToken();
    if (!token) return null;
    try {
        const part = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
        return JSON.parse(atob(part));
    } catch {
        return null;
    }
}

function can(permission) {
    const user = payload();
    return Boolean(user) && Array.isArray(user.permissions) && user.permissions.includes(permission);
}

// --- Login con Auth0 (flujo implícito del curso) ---
function redirectUri() {
    return `${window.location.origin}/`;
}

// crypto.randomUUID solo existe en HTTPS o localhost; getRandomValues funciona siempre
function randomState() {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

function loginUrl() {
    const state = randomState();
    sessionStorage.setItem(STATE_KEY, state);
    const params = new URLSearchParams({
        audience: window.AUTH0.audience,
        response_type: "token",
        client_id: window.AUTH0.clientId,
        redirect_uri: redirectUri(),
        state,
    });
    return `https://${window.AUTH0.domain}/authorize?${params}`;
}

// Al volver de Auth0 el token llega en el fragmento de la URL (#access_token=...)
function readTokenFromFragment() {
    const params = new URLSearchParams(window.location.hash.slice(1));
    if (!params.has("access_token") && !params.has("error")) return;

    // Quitar el token de la barra de direcciones y del historial
    history.replaceState(null, "", window.location.pathname);

    const expected = sessionStorage.getItem(STATE_KEY);
    sessionStorage.removeItem(STATE_KEY);

    if (params.has("error")) {
        show(params.get("error_description") || params.get("error"));
    } else if (!expected || params.get("state") !== expected) {
        show("The login response does not match this browser. Please sign in again.");
    } else {
        setToken(params.get("access_token"));
    }
}

// --- Peticiones a la API ---
async function api(path, { method = "GET", body = null } = {}) {
    const headers = { "Content-Type": "application/json" };
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(path, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json().catch(() => ({}));

    if (res.status === 401 && token) {
        setToken(null); // expirado o inválido: vuelta al login
        render();
    }
    if (!res.ok) throw new Error(data.message || `HTTP ${res.status}`);
    return data;
}

// --- Mensajes y vistas ---
function show(message, kind = "error") {
    const box = $("message");
    box.textContent = message;
    box.className = `flash flash-${kind}`;
    box.hidden = !message;
}

async function run(action) {
    show("");
    try {
        await action();
    } catch (err) {
        show(err.message);
    }
}

async function render() {
    const user = payload();
    const signedIn = Boolean(user) && user.exp * 1000 > Date.now() && Array.isArray(user.permissions);
    if (!signedIn) setToken(null);

    $("auth-view").hidden = signedIn;
    $("todos-view").hidden = !signedIn;
    $("logout").hidden = !signedIn;
    $("who").textContent = signedIn ? (can("delete:todos") ? "admin" : "user") : "";

    if (signedIn) await loadTodos();
}

async function loadTodos() {
    const { todos } = await api("/api/todos");
    $("todo-list").replaceChildren(...todos.map(todoItem));
    $("count").textContent = `(${todos.length})`;
    $("empty").hidden = todos.length === 0;
}

// --- Interfaz de tareas ---
function button(text, className, action) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = className;
    b.textContent = text;
    b.addEventListener("click", () => run(async () => {
        if (await action()) await loadTodos();
    }));
    return b;
}

function todoItem(todo) {
    const li = document.createElement("li");
    li.className = "todo-item" + (todo.completed ? " completed" : "");

    const check = button(todo.completed ? "☑" : "☐", "checkbox", () =>
        api(`/api/todos/${todo.id}`, { method: "PATCH", body: { completed: !todo.completed } })
    );
    check.setAttribute("aria-label", "Toggle completed");

    const body = document.createElement("div");
    body.className = "todo-body";

    const title = document.createElement("span");
    title.className = "todo-title";
    title.textContent = todo.title;
    body.append(title);

    if (todo.description) {
        const description = document.createElement("p");
        description.className = "todo-description";
        description.textContent = todo.description;
        body.append(description);
    }

    const actions = document.createElement("div");
    actions.className = "todo-actions";

    if (can("delete:todos")) {
        actions.append(button("Delete", "btn btn-small btn-danger", () =>
            confirm("Delete this todo?") && api(`/api/todos/${todo.id}`, { method: "DELETE" })
        ));
    }

    li.append(check, body, actions);
    return li;
}

// --- Eventos ---
$("login").addEventListener("click", () => {
    window.location.assign(loginUrl());
});

$("create-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const fields = event.target.elements;
    run(async () => {
        await api("/api/todos", {
            method: "POST",
            body: { title: fields.title.value, description: fields.description.value }
        });
        event.target.reset();
        await loadTodos();
    });
});

// Borra el token y cierra también la sesión de Auth0; si no, "Sign in" entraría sin pedir contraseña
$("logout").addEventListener("click", () => {
    setToken(null);
    const params = new URLSearchParams({ client_id: window.AUTH0.clientId, returnTo: redirectUri() });
    window.location.assign(`https://${window.AUTH0.domain}/v2/logout?${params}`);
});

readTokenFromFragment();
run(render);