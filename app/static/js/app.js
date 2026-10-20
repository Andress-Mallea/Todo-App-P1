const TOKEN_KEY = "access_token";
const $ = (id) => document.getElementById(id);

// --- Funciones del Token ---
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

// --- Mensajes y Vistas ---
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
    $("who").textContent = signedIn ? `${user.username} (${user.role})` : "";

    if (signedIn) await loadTodos();
}

async function loadTodos() {
    const { todos } = await api("/api/todos");
    $("todo-list").replaceChildren(...todos.map(todoItem));
    $("count").textContent = `(${todos.length})`;
    $("empty").hidden = todos.length === 0;
}

// --- Interfaz de Tareas ---
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

// --- Eventos de Login y Registro ---
function credentials() {
    return { username: $("username").value, password: $("password").value };
}

async function signIn() {
    const { access_token } = await api("/auth/login", { method: "POST", body: credentials() });
    setToken(access_token);
    $("login-form").reset();
    await render();
}

$("login-form").addEventListener("submit", (event) => {
    event.preventDefault();
    run(signIn);
});

$("register").addEventListener("click", () => run(async () => {
    if (!$("login-form").reportValidity()) return;
    await api("/auth/register", { method: "POST", body: credentials() });
    await signIn();
    show("Account created.", "success");
}));

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

$("logout").addEventListener("click", () => {
    setToken(null);
    render();
    show("Signed out.", "success");
});

run(render);