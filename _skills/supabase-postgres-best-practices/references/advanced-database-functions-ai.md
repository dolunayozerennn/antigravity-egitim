# Supabase Database Functions (AI Best Practices)

When creating or modifying PostgreSQL functions and stored procedures for Supabase, strictly follow these security and performance guidelines.

## Best Practices

1. **Default to SECURITY INVOKER:** Always define functions with `SECURITY INVOKER` unless there is a specific, well-documented need to elevate privileges. `SECURITY INVOKER` ensures the function runs with the permissions of the user calling it, maintaining the integrity of RLS policies.
2. **Mandatory Search Path:** ALWAYS specify `SET search_path = ''` (empty string) in function definitions. This is a critical security measure that prevents search path injection attacks, where a malicious user could trick the function into executing an object in a schema they control instead of the intended object.
3. **Explicit Typing:** Provide explicit and clear types for all arguments and return values. Avoid `record` or `anyelement` if a concrete type or a `TABLE()` return type can be used, as it improves GraphQL/PostgREST generation and client-side typings.
4. **Volatility Categories:** Explicitly mark functions as `VOLATILE` (default, can modify data), `STABLE` (cannot modify data, results depend on DB state), or `IMMUTABLE` (cannot modify data, results depend ONLY on arguments). Using `STABLE` or `IMMUTABLE` correctly allows Postgres to optimize query plans significantly.

## Example: Incorrect

```sql
-- INCORRECT: Missing security context and search_path
CREATE OR REPLACE FUNCTION get_user_profiles(input_role text)
RETURNS SETOF public.profiles
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY SELECT * FROM public.profiles WHERE role = input_role;
END;
$$;
```

## Example: Correct

```sql
-- CORRECT: Explicit security invoker, search_path, and volatility
CREATE OR REPLACE FUNCTION get_user_profiles(input_role text)
RETURNS SETOF public.profiles
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
STABLE
AS $$
BEGIN
  RETURN QUERY SELECT * FROM public.profiles WHERE role = input_role;
END;
$$;
```

## Context

Failing to set the `search_path` leaves functions vulnerable to local privilege escalation. Postgres searches for unqualified objects (like tables or other functions) in the schemas listed in `search_path`. A malicious user could create an object with the same name in the `public` schema (if they have create rights) to hijack the execution flow.
