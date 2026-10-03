-- Jeu de test FICTIF (aucune donnée personnelle réelle) inspiré du planning MATRiCE.
DROP TABLE IF EXISTS seance;

CREATE TABLE seance (
    id           SERIAL PRIMARY KEY,
    date_seance  DATE        NOT NULL,
    demi_journee VARCHAR(10) NOT NULL CHECK (demi_journee IN ('matin', 'apres-midi')),
    groupe       VARCHAR(50) NOT NULL,
    formateur    VARCHAR(50) NOT NULL,
    titre        VARCHAR(100) NOT NULL
);

INSERT INTO seance (date_seance, demi_journee, groupe, formateur, titre) VALUES
    ('2026-10-19', 'matin',      'B3D', 'Formateur A', 'HTML & structure'),
    ('2026-10-19', 'apres-midi', 'B3D', 'Formateur A', 'CSS & mise en page'),
    ('2026-10-20', 'matin',      'B3D', 'Formateur B', 'Responsive & formulaires'),
    ('2026-10-21', 'matin',      'B3D', 'Formateur C', 'Accessibilité numérique'),
    ('2026-10-22', 'matin',      'B3D', 'Formateur D', 'UX & tests utilisateurs'),
    ('2026-10-23', 'matin',      'B3D', 'Formateur B', 'Git & collaboration');
