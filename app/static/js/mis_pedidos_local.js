async function cargarPedidosLocales() {
    const token = sessionStorage.getItem("local_jwt_token");
    const mensaje = document.getElementById("mensaje-pedidos");
    const tabla = document.getElementById("tabla-pedidos");
    const lista = document.getElementById("lista-pedidos");

    if (!token) {
        mensaje.textContent = "Debes iniciar sesión.";
        window.location.href = "/auth/local/entrar";
        return;
    }

    try {
        const respuesta = await fetch("/pedidos", {
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
            throw new Error(`Error HTTP ${respuesta.status}`);
        }

        const datos = await respuesta.json();

        lista.replaceChildren();

        if (datos.pedidos.length === 0) {
            mensaje.textContent = "Todavía no tienes pedidos.";
            return;
        }

        for (const pedido of datos.pedidos) {
            const fila = document.createElement("tr");

            const valores = [
                pedido.id,
                new Date(pedido.fecha).toLocaleString(),
                pedido.estado,
                `Bs ${pedido.total}`
            ];

            for (const valor of valores) {
                const celda = document.createElement("td");
                celda.textContent = valor;
                fila.appendChild(celda);
            }

            lista.appendChild(fila);
            const celdaAcciones = document.createElement("td");

            const enlaceDetalle = document.createElement("a");

            enlaceDetalle.href = `/mis-pedidos-local/${pedido.id}`;
            enlaceDetalle.textContent = "Ver detalle";

            celdaAcciones.appendChild(enlaceDetalle);
            fila.appendChild(celdaAcciones);
        }

        mensaje.textContent = "";
        tabla.hidden = false;

    } catch (error) {
        mensaje.textContent = "No se pudieron cargar los pedidos.";
        console.error(error);
    }
}

cargarPedidosLocales();