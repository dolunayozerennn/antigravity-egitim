# Supabase RLS Policies (AI Best Practices)

Row-Level Security (RLS) is critical for securing data in Supabase. When creating or reviewing RLS policies, adhere strictly to these official guidelines.

## Best Practices

1. **Explicit Policies per Operation:** Recommend 4 separate policies per table (one each for `select`, `insert`, `update`, and `delete`). Avoid using `ALL` policies as they often lead to logic errors and security gaps.
2. **Use PERMISSIVE Policies:** Always default to `PERMISSIVE` policies (the default behavior in Postgres). Avoid `RESTRICTIVE` policies unless explicitly required for highly specialized compliance reasons, as they are evaluated using AND logic and can cause unexpected lockouts.
3. **Use `auth.uid()`:** Always use `auth.uid()` to identify the current user in Supabase. Never use `current_user` for authentication checks, as it refers to the Postgres role (which is usually `authenticated` or `anon` in Supabase) rather than the specific user ID.
4. **Optimize with Functions:** If an RLS policy requires joining another table (e.g., checking permissions in a user_roles table), wrap the check in a `security definer` database function. RLS policies with direct joins execute for *every row* and cause massive performance degradation.
5. **Index Foreign Keys:** Ensure any column used in an RLS policy (especially foreign keys to `auth.users` or tenant IDs) has an index.

## Example: Incorrect

```sql
-- INCORRECT: Uses ALL policy, joins within the policy, and uses current_user
CREATE POLICY "Users can manage their own team's data"
ON public.team_data
FOR ALL
USING (
  team_id IN (
    SELECT team_id FROM public.team_members WHERE user_email = current_user
  )
);
```

## Example: Correct

```sql
-- CORRECT: Separate policy, uses auth.uid(), avoids slow joins by using a wrapper function
-- First, create the wrapper function
CREATE OR REPLACE FUNCTION public.get_user_teams()
RETURNS SETOF uuid
LANGUAGE sql
SECURITY DEFINER
SET search_path = ''
AS $$
  SELECT team_id FROM public.team_members WHERE user_id = auth.uid();
$$;

-- Second, create a specific SELECT policy
CREATE POLICY "Users can view their team's data"
ON public.team_data
FOR SELECT
USING (
  team_id IN (SELECT public.get_user_teams())
);
```

## Context

Using `security definer` functions for complex RLS checks allows Postgres to evaluate the condition much faster than executing a subquery join on every row. Always ensure the `security definer` function has `SET search_path = ''` to prevent security vulnerabilities.
