document.addEventListener("DOMContentLoaded", async () => {
    const token = sessionStorage.getItem("local_jwt_token");
    const mensaje = document.getElementById("mensaje-admin");
    const panel = document.getElementById("panel-admin-local");
    const listaRestaurantes = document.getElementById("lista-restaurantes");
    const listaPlatos = document.getElementById("lista-platos");
    const formCrearRestaurante = document.getElementById(
        "form-crear-restaurante"
    );
    const formCrearPlato = document.getElementById("form-crear-plato");
    const selectRestaurantePlato = document.getElementById(
        "select-restaurante-plato"
    );
    if (!token) {
        mensaje.textContent = "Debes iniciar sesión para administrar la carta.";
        return;
    }

    try {
        const respuesta = await fetch("/administrar/", {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (respuesta.status === 401) {
            mensaje.textContent = "Tu sesión expiró. Inicia sesión nuevamente.";
            return;
        }

        if (respuesta.status === 403) {
            mensaje.textContent = "403 - No tienes permisos de administrador.";
            return;
        }

        if (!respuesta.ok) {
            throw new Error(`Error HTTP ${respuesta.status}`);
        }

        const datos = await respuesta.json();
        // Cargar restaurantes disponibles en el formulario de platos.
        selectRestaurantePlato.replaceChildren();

        const opcionInicial = document.createElement("option");
        opcionInicial.value = "";
        opcionInicial.textContent = "Selecciona un restaurante";
        selectRestaurantePlato.appendChild(opcionInicial);

        datos.restaurantes.forEach(restaurante => {
            const opcion = document.createElement("option");
            opcion.value = restaurante.id;
            opcion.textContent = restaurante.nombre;

            selectRestaurantePlato.appendChild(opcion);
        });
        panel.hidden = false;
        mensaje.textContent = "";

        // Mostrar restaurantes.
        listaRestaurantes.replaceChildren();

        if (!datos.restaurantes.length) {
            listaRestaurantes.textContent = "No hay restaurantes registrados.";
        }

        datos.restaurantes.forEach(restaurante => {
            const articulo = document.createElement("article");

            const titulo = document.createElement("h4");
            titulo.textContent = restaurante.nombre;

            const descripcion = document.createElement("p");
            descripcion.textContent = restaurante.descripcion || "";

            const botonEditar = document.createElement("button");
            botonEditar.type = "button";
            botonEditar.textContent = "Editar";

            botonEditar.addEventListener("click", async () => {
                const nuevoNombre = prompt(
                    "Nuevo nombre del restaurante:",
                    restaurante.nombre
                );

                if (nuevoNombre === null) return;

                const nuevaDescripcion = prompt(
                    "Nueva descripción:",
                    restaurante.descripcion || ""
                );

                if (nuevaDescripcion === null) return;

                if (!nuevoNombre.trim() || nuevoNombre.length > 150) {
                    mensaje.textContent = "El nombre debe tener entre 1 y 150 caracteres.";
                    return;
                }

                botonEditar.disabled = true;

                try {
                    const respuesta = await fetch(
                        `/administrar/restaurantes/${restaurante.id}/editar`,
                        {
                            method: "POST",
                            headers: {
                                Authorization: `Bearer ${token}`
                            },
                            body: new URLSearchParams({
                                nombre: nuevoNombre.trim(),
                                descripcion: nuevaDescripcion
                            })
                        }
                    );

                    if (!respuesta.ok) {
                        throw new Error(
                            `No se pudo editar el restaurante (${respuesta.status})`
                        );
                    }

                    const datos = await respuesta.json();

                    titulo.textContent = datos.restaurante.nombre;
                    descripcion.textContent = datos.restaurante.descripcion || "";

                    restaurante.nombre = datos.restaurante.nombre;
                    restaurante.descripcion = datos.restaurante.descripcion;

                    mensaje.textContent = datos.message;

                } catch (error) {
                    mensaje.textContent = error.message;
                } finally {
                    botonEditar.disabled = false;
                }
            });

            const botonEliminar = document.createElement("button");
            botonEliminar.type = "button";
            botonEliminar.textContent = "Eliminar";

            botonEliminar.addEventListener("click", async () => {

                const confirmar = confirm(
                    `¿Estás seguro de eliminar el restaurante "${restaurante.nombre}"?`
                );

                if (!confirmar) return;

                botonEliminar.disabled = true;

                try {
                    const respuesta = await fetch(
                        `/administrar/restaurantes/${restaurante.id}/eliminar`,
                        {
                            method: "POST",
                            headers: {
                                Authorization: `Bearer ${token}`
                            }
                        }
                    );

                    if (respuesta.status === 409) {
                        mensaje.textContent =
                            "No se puede eliminar el restaurante porque tiene platos o registros relacionados.";
                        return;
                    }

                    if (respuesta.status === 401 || respuesta.status === 403) {
                        mensaje.textContent = "No tienes autorización para eliminar restaurantes.";
                        return;
                    }

                    if (!respuesta.ok) {
                        throw new Error(
                            `No se pudo eliminar el restaurante (${respuesta.status})`
                        );
                    }

                    const datos = await respuesta.json();

                    articulo.remove();

                    mensaje.textContent = datos.message;

                } catch (error) {
                    mensaje.textContent = error.message;
                } finally {
                    botonEliminar.disabled = false;
                }
            });

            if (datos.puede_eliminar) {
                articulo.append(titulo, descripcion, botonEditar, botonEliminar);
            } else {
                articulo.append(titulo, descripcion, botonEditar);
            }

            listaRestaurantes.appendChild(articulo);
                    });

                    // Mostrar platos.
                    listaPlatos.replaceChildren();

                    if (!datos.platos.length) {
                        listaPlatos.textContent = "No hay platos registrados.";
                    }

                    datos.platos.forEach(plato => {
                        const articulo = document.createElement("article");

                        const titulo = document.createElement("h4");
                        titulo.textContent = plato.nombre;

                        const detalle = document.createElement("p");
                        detalle.textContent =
                            `${plato.restaurante} - Bs ${plato.precio} - ` +
                            (plato.disponible ? "Disponible" : "No disponible");

                        const botonEditar = document.createElement("button");
                        botonEditar.type = "button";
                        botonEditar.textContent = "Editar";

                        botonEditar.addEventListener("click", async () => {

                            const nuevoNombre = prompt(
                                "Nombre del plato:",
                                plato.nombre
                            );

                            if (nuevoNombre === null) return;

                            const nuevaDescripcion = prompt(
                                "Descripción:",
                                plato.descripcion || ""
                            );

                            if (nuevaDescripcion === null) return;

                            const nuevoPrecio = prompt(
                                "Precio del plato (Bs):",
                                plato.precio
                            );

                            if (nuevoPrecio === null) return;

                            const nuevoRestaurante = prompt(
                                "ID del restaurante:",
                                plato.restaurante_id
                            );

                            if (nuevoRestaurante === null) return;

                            const disponible = confirm(
                                "¿El plato estará disponible?"
                            );

                            if (!nuevoNombre.trim() || nuevoNombre.trim().length > 150) {
                                mensaje.textContent =
                                    "El nombre debe tener entre 1 y 150 caracteres.";
                                return;
                            }

                            const precioNumero = Number(nuevoPrecio);
                            const restauranteNumero = Number(nuevoRestaurante);

                            if (
                                !Number.isFinite(precioNumero) ||
                                precioNumero < 0 ||
                                !/^\d+(\.\d{1,2})?$/.test(nuevoPrecio.trim())
                            ) {
                                mensaje.textContent = "Introduce un precio válido.";
                                return;
                            }

                            if (!Number.isInteger(restauranteNumero) || restauranteNumero <= 0) {
                                mensaje.textContent = "Selecciona un ID de restaurante válido.";
                                return;
                            }

                            botonEditar.disabled = true;

                            try {
                                const campos = new URLSearchParams({
                                    nombre: nuevoNombre.trim(),
                                    descripcion: nuevaDescripcion,
                                    precio: nuevoPrecio.trim(),
                                    restaurante_id: String(restauranteNumero)
                                });

                                if (disponible) {
                                    campos.append("disponible", "on");
                                }

                                const respuesta = await fetch(
                                    `/administrar/platos/${plato.id}/editar`,
                                    {
                                        method: "POST",
                                        headers: {
                                            Authorization: `Bearer ${token}`
                                        },
                                        body: campos
                                    }
                                );

                                if (!respuesta.ok) {
                                    throw new Error(
                                        `No se pudo editar el plato (${respuesta.status})`
                                    );
                                }

                                const resultado = await respuesta.json();

                                mensaje.textContent = resultado.message;

                                // Recargar los datos para reflejar el restaurante,
                                // precio y disponibilidad actualizados.
                                window.location.reload();

                            } catch (error) {
                                mensaje.textContent = error.message;
                            } finally {
                                botonEditar.disabled = false;
                            }
                        });

                        const botonEliminar = document.createElement("button");
                        botonEliminar.type = "button";
                        botonEliminar.textContent = "Eliminar";

                        botonEliminar.addEventListener("click", async () => {

                            const confirmar = confirm(
                                `¿Estás seguro de eliminar el plato "${plato.nombre}"?`
                            );

                            if (!confirmar) return;

                            botonEliminar.disabled = true;

                            try {
                                const respuesta = await fetch(
                                    `/administrar/platos/${plato.id}/eliminar`,
                                    {
                                        method: "POST",
                                        headers: {
                                            Authorization: `Bearer ${token}`
                                        }
                                    }
                                );

                                if (respuesta.status === 409) {
                                    mensaje.textContent =
                                        "No se puede eliminar el plato porque está asociado a pedidos históricos.";
                                    return;
                                }

                                if (respuesta.status === 401) {
                                    mensaje.textContent =
                                        "Tu sesión expiró. Inicia sesión nuevamente.";
                                    return;
                                }

                                if (respuesta.status === 403) {
                                    mensaje.textContent =
                                        "No tienes permisos para eliminar platos.";
                                    return;
                                }

                                if (!respuesta.ok) {
                                    throw new Error(
                                        `No se pudo eliminar el plato (${respuesta.status})`
                                    );
                                }

                                const resultado = await respuesta.json();

                                // Retirar el plato de la interfaz después de confirmar
                                // que PostgreSQL completó la eliminación.
                                articulo.remove();

                                mensaje.textContent = resultado.message;

                            } catch (error) {
                                mensaje.textContent = error.message;
                            } finally {
                                botonEliminar.disabled = false;
                            }
                        });

                        articulo.append(titulo, detalle, botonEditar);

                        if (datos.puede_eliminar) {
                            articulo.appendChild(botonEliminar);
                        }

                        listaPlatos.appendChild(articulo);
        });

    } catch (error) {
        mensaje.textContent = `Error al cargar la administración: ${error.message}`;
    }
    formCrearRestaurante.addEventListener("submit", async (event) => {
        event.preventDefault();

        const boton = formCrearRestaurante.querySelector(
            'button[type="submit"]'
        );

        boton.disabled = true;

        try {
            const respuesta = await fetch(
                "/administrar/restaurantes/nuevo",
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`
                    },
                    body: new FormData(formCrearRestaurante)
                }
            );

            if (!respuesta.ok) {
                throw new Error(
                    `No se pudo crear el restaurante (${respuesta.status})`
                );
            }

            const datos = await respuesta.json();
            
            mensaje.textContent = datos.message;
            formCrearRestaurante.reset();

            // Actualizar las listas con los datos actuales.
            window.location.reload();

        } catch (error) {
            mensaje.textContent = error.message;
        } finally {
            boton.disabled = false;
        }
    });
    formCrearPlato.addEventListener("submit", async (event) => {
        event.preventDefault();

        const boton = formCrearPlato.querySelector('button[type="submit"]');
        boton.disabled = true;

        try {
            const respuesta = await fetch("/administrar/platos/nuevo", {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`
                },
                body: new FormData(formCrearPlato)
            });

            if (respuesta.status === 401) {
                mensaje.textContent = "Tu sesión expiró. Inicia sesión nuevamente.";
                return;
            }

            if (respuesta.status === 403) {
                mensaje.textContent = "No tienes permisos para crear platos.";
                return;
            }

            if (!respuesta.ok) {
                throw new Error(
                    `No se pudo crear el plato (${respuesta.status})`
                );
            }

            const resultado = await respuesta.json();

            mensaje.textContent = resultado.message;

            formCrearPlato.reset();

            // Volver a consultar restaurantes y platos actualizados.
            window.location.reload();

        } catch (error) {
            mensaje.textContent = error.message;
        } finally {
            boton.disabled = false;
        }
    });
});