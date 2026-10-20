-- ==============================================================================
-- 1. CONFIGURACIÓN INICIAL: Esquema y Extensiones
-- ==============================================================================

-- Aislamiento de las tablas fuera del esquema public
CREATE SCHEMA IF NOT EXISTS content;

-- Habilitar la generación automática de UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- 2. DEFINICIÓN DE TIPOS ESTRICTOS (ENUMs)
-- ==============================================================================

CREATE TYPE content.table_status AS ENUM ('AVAILABLE', 'OCCUPIED', 'RESERVED');
CREATE TYPE content.order_type AS ENUM ('DINE_IN', 'TAKEOUT');
CREATE TYPE content.order_status AS ENUM ('PENDING', 'PREPARING', 'READY', 'COMPLETED', 'CANCELED');

-- ==============================================================================
-- 3. CREACIÓN DE TABLAS
-- ==============================================================================

-- Categorías del Menú
CREATE TABLE content.category (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Productos (Menú)
CREATE TABLE content.product (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID NOT NULL,
    name VARCHAR(150) NOT NULL,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP, -- Borrado lógico
    CONSTRAINT fk_category FOREIGN KEY (category_id) REFERENCES content.category(id) ON DELETE RESTRICT
);

-- Clientes
CREATE TABLE content.customer (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mesas del Restaurante
CREATE TABLE content.dining_table (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_number INT NOT NULL UNIQUE CHECK (table_number > 0),
    capacity INT NOT NULL CHECK (capacity > 0),
    current_status content.table_status DEFAULT 'AVAILABLE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cabecera del Pedido (Soporta Dine-in y Takeout)
CREATE TABLE content.customer_order (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID,
    table_id UUID, -- Nullable para pedidos TAKEOUT
    order_type content.order_type NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00 CHECK (total_amount >= 0),
    status content.order_status DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES content.customer(id) ON DELETE SET NULL,
    CONSTRAINT fk_table FOREIGN KEY (table_id) REFERENCES content.dining_table(id) ON DELETE SET NULL
);

-- Detalle del Pedido (Líneas)
CREATE TABLE content.order_line (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL,
    product_id UUID NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_order FOREIGN KEY (order_id) REFERENCES content.customer_order(id) ON DELETE CASCADE,
    CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES content.product(id) ON DELETE RESTRICT
);

-- Promociones (Reglas de negocio)
CREATE TABLE content.promotion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL UNIQUE,
    discount_percentage DECIMAL(5, 2) NOT NULL CHECK (discount_percentage >= 0 AND discount_percentage <= 100),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Relación Promoción-Producto (Muchos a Muchos)
CREATE TABLE content.promotion_product (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    promotion_id UUID NOT NULL,
    product_id UUID NOT NULL,
    CONSTRAINT fk_promotion FOREIGN KEY (promotion_id) REFERENCES content.promotion(id) ON DELETE CASCADE,
    CONSTRAINT fk_promoted_product FOREIGN KEY (product_id) REFERENCES content.product(id) ON DELETE CASCADE,
    CONSTRAINT uq_promotion_product UNIQUE (promotion_id, product_id) -- Evita duplicar el mismo producto en la misma promo
);
-- ==============================================================================
-- 4. ÍNDICES DE RENDIMIENTO (Llaves Foráneas)
-- ==============================================================================

CREATE INDEX idx_product_category ON content.product(category_id);
CREATE INDEX idx_order_customer ON content.customer_order(customer_id);
CREATE INDEX idx_order_table ON content.customer_order(table_id);
CREATE INDEX idx_orderline_order ON content.order_line(order_id);
CREATE INDEX idx_orderline_product ON content.order_line(product_id);
-- ==============================================================================
-- 5. ÍNDICES DE NEGOCIO (Filtros comunes)
-- ==============================================================================

-- Acelera la búsqueda de pedidos por su estado actual para las pantallas de la cocina
CREATE INDEX idx_order_status ON content.customer_order(status);

-- Acelera la generación de reportes financieros por fecha
CREATE INDEX idx_order_date ON content.customer_order(created_at);

-- Acelera la carga del menú para los clientes (solo mostrar productos activos)
CREATE INDEX idx_product_active ON content.product(is_active);