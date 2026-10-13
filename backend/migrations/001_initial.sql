CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE products (
    id              bigserial PRIMARY KEY,
    source          text NOT NULL CHECK (source IN ('sephora', 'obf')),
    source_id       text NOT NULL,
    barcode         text UNIQUE,
    name            text NOT NULL,
    brand           text,
    category        text,
    ingredients_raw text,
    has_ingredients boolean NOT NULL DEFAULT false,
    UNIQUE (source, source_id)
);

CREATE TABLE product_ingredients (
    product_id bigint NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    position   int    NOT NULL,
    name       text   NOT NULL,
    PRIMARY KEY (product_id, position)
);

CREATE INDEX product_ingredients_name_idx ON product_ingredients (name);

-- user_id is the Supabase Auth user ID; no foreign key, since local Postgres has no auth schema.
CREATE TABLE profiles (
    user_id           uuid PRIMARY KEY,
    skin_type         text,
    age_band          text,
    sensitivities     text[] NOT NULL DEFAULT '{}',
    avoid_ingredients text[] NOT NULL DEFAULT '{}',
    updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE shelf_items (
    user_id    uuid   NOT NULL,
    product_id bigint NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    added_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, product_id)
);

CREATE TABLE routine_items (
    user_id    uuid   NOT NULL,
    product_id bigint NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    slot       text   NOT NULL CHECK (slot IN ('am', 'pm')),
    position   int    NOT NULL DEFAULT 0,
    added_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, slot, product_id)
);
