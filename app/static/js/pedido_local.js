const token = sessionStorage.getItem("local_jwt_token");

const mensaje = document.getElementById("mensaje-detalle");
const contenido = document.getElementById("contenido-pedido");
const botonCancelar = document.getElementById("cancelar-pedido");

async function cargarDetalle() {
    if (!token) {
        window.location.href = "/auth/local/entrar";
        return;
    }

    try {
        const respuesta = await fetch(`/pedidos/${PEDIDO_ID}`, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (respuesta.status === 401) {
            sessionStorage.removeItem("local_jwt_token");
            window.location.href = "/auth/local/entrar";
            return;
        }

        if (!respuesta.ok) {
            throw new Error(`HTTP ${respuesta.status}`);
        }

        const datos = await respuesta.json();
        const pedido = datos.pedido;

        document.getElementById("restaurante").textContent =
            pedido.restaurante;

        document.getElementById("estado").textContent =
            pedido.estado;

        document.getElementById("fecha").textContent =
            new Date(pedido.fecha).toLocaleString();

        document.getElementById("total").textContent =
            pedido.total;

        const tabla = document.getElementById("items-pedido");
        tabla.replaceChildren();

        for (const item of pedido.items) {
            const fila = document.createElement("tr");

            const valores = [
                item.plato,
                item.cantidad,
                `Bs ${item.precio_unitario}`,
                `Bs ${item.subtotal}`
            ];

            for (const valor of valores) {
                const celda = document.createElement("td");
                celda.textContent = valor;
                fila.appendChild(celda);
            }

            tabla.appendChild(fila);
        }

        botonCancelar.hidden = pedido.estado !== "pendiente";

        mensaje.textContent = "";
        contenido.hidden = false;

    } catch (error) {
        mensaje.textContent = "No se pudo cargar el detalle del pedido.";
        console.error(error);
    }
}

botonCancelar.addEventListener("click", async () => {
    if (!confirm("¿Estás seguro de cancelar este pedido?")) {
        return;
    }

    botonCancelar.disabled = true;

    try {
        const respuesta = await fetch(
            `/pedidos/${PEDIDO_ID}/cancelar`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`
                },
                redirect: "manual"
            }
        );

        if (respuesta.status === 401) {
            sessionStorage.removeItem("local_jwt_token");
            window.location.href = "/auth/local/entrar";
            return;
        }

        if (!respuesta.ok) {
            throw new Error(`HTTP ${respuesta.status}`);
        }

        await cargarDetalle();

    } catch (error) {
        mensaje.textContent = "No se pudo cancelar el pedido.";
        console.error(error);
    } finally {
        botonCancelar.disabled = false;
    }
});

cargarDetalle();