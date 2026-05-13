-- Add admin user to NBS Archive groups (Odoo 19 compatible)
INSERT INTO res_groups_users_rel (gid, uid)
SELECT rg.id, 2
FROM res_groups rg
WHERE rg.name->>'en_US' IN ('NBS Archive Administrator', 'NBS Archive Manager', 'NBS Archive User')
   OR rg.name::text LIKE '%NBS Archive%'
ON CONFLICT DO NOTHING;

-- Verify
SELECT u.login, rg.name::text as group_name
FROM res_users u
JOIN res_groups_users_rel rel ON rel.uid = u.id
JOIN res_groups rg ON rg.id = rel.gid
WHERE u.id = 2;
