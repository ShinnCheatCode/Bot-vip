-- Publishable key không INSERT được vì RLS.
-- Dùng secret/service_role trên GitHub Actions (khuyến nghị).
--
-- Nếu muốn hạn chế hơn, tạo RPC chỉ cho phép tạo đúng gói 1 giờ:

create or replace function public.create_group_key_1h(p_key text)
returns public.keys
language plpgsql
security definer
set search_path = public
as $$
declare
  row public.keys;
begin
  insert into public.keys (
    key, device_id, max_devices, expires_at,
    activated_at, is_used, is_vip, role, label
  ) values (
    p_key,
    null,
    1,
    timezone('utc', now()) + interval '1 hour',
    null,
    false,
    false,
    'member',
    'group-free'
  )
  returning * into row;
  return row;
end;
$$;
