-- Rules-based score from app/scoring.py. NULL for products without ingredients ("Not enough data").
ALTER TABLE products
    ADD COLUMN score smallint CHECK (score BETWEEN 0 AND 100),
    ADD COLUMN grade text;
