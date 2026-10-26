document.addEventListener("DOMContentLoaded", () => {

    const lista = document.getElementById("lista-pedidos-cocina");
    const mensaje = document.getElementById("mensaje-cocina");

    const token = sessionStorage.getItem("local_jwt_token");

    if (!token) {
        mensaje.textContent = "Debes iniciar sesión con JWT.";
        return;
    }

    async function cargarPedidos() {
        mensaje.textContent = "Cargando pedidos...";
        lista.replaceChildren();

        try {
            const respuesta = await fetch("/cocina", {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });

            if (respuesta.status === 401) {
                mensaje.textContent = "Tu sesión expiró. Inicia sesión nuevamente.";
                return;
            }

            if (respuesta.status === 403) {
                mensaje.textContent = "403 - No tienes permisos para acceder a cocina.";
                return;
            }

            if (!respuesta.ok) {
                throw new Error(`Error HTTP ${respuesta.status}`);
            }

            const datos = await respuesta.json();

            if (datos.pedidos.length === 0) {
                mensaje.textContent = "No hay pedidos activos.";
                return;
            }

            mensaje.textContent = "";

            datos.pedidos.forEach(pedido => {

                const articulo = document.createElement("article");

                const titulo = document.createElement("h3");
                titulo.textContent = `Pedido #${pedido.id}`;

                const restaurante = document.createElement("p");
                restaurante.textContent = `Restaurante: ${pedido.restaurante}`;

                const estado = document.createElement("p");
                estado.textContent = `Estado: ${pedido.estado}`;

                const productos = document.createElement("ul");

                pedido.items.forEach(item => {
                    const elemento = document.createElement("li");
                    elemento.textContent = `${item.cantidad} × ${item.plato}`;
                    productos.appendChild(elemento);
                });

                articulo.append(
                    titulo,
                    restaurante,
                    estado,
                    productos
                );

                if (datos.puede_avanzar) {
                    const boton = document.createElement("button");
                    boton.type = "button";
                    boton.textContent = "Avanzar estado";

                    boton.addEventListener("click", async () => {
                        boton.disabled = true;

                        try {
                            const respuesta = await fetch(
                                `/cocina/pedidos/${pedido.id}/avanzar`,
                                {
                                    method: "POST",
                                    headers: {
                                        Authorization: `Bearer ${token}`
                                    }
                                }
                            );

                            if (!respuesta.ok) {
                                throw new Error(
                                    `No se pudo avanzar el pedido (${respuesta.status})`
                                );
                            }

                            await cargarPedidos();

                        } catch (error) {
                            mensaje.textContent = error.message;
                            boton.disabled = false;
                        }
                    });

                    articulo.appendChild(boton);
                }

                lista.appendChild(articulo);
            });

        } catch (error) {
            mensaje.textContent = `Error al cargar pedidos: ${error.message}`;
        }
    }

    cargarPedidos();
});