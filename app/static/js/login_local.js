const formulario = document.getElementById("form-login-local");
const mensaje = document.getElementById("mensaje-login");
const botonRegistro = document.getElementById("btn-registro");

function credenciales() {
    return {
        username: document.getElementById("username").value,
        password: document.getElementById("password").value
    };
}

async function enviarCredenciales(endpoint) {
    mensaje.textContent = "";

    try {
        const respuesta = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(credenciales())
        });

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(datos.message || "Error de autenticación");
        }

        return datos;

    } catch (error) {
        mensaje.textContent = error.message;
        return null;
    }
}

formulario.addEventListener("submit", async (event) => {
    event.preventDefault();

    const datos = await enviarCredenciales("/auth/local/login");

    if (!datos) return;

    sessionStorage.setItem("local_jwt_token", datos.access_token);

    window.location.href = "/restaurantes";
});

botonRegistro.addEventListener("click", async () => {
    if (!formulario.reportValidity()) return;

    const registro = await enviarCredenciales("/auth/local/register");

    if (!registro) return;

    const login = await enviarCredenciales("/auth/local/login");

    if (!login) return;

    sessionStorage.setItem("local_jwt_token", login.access_token);

    window.location.href = "/restaurantes";
});