from supabase_client import supabase


response = (
    supabase
    .table("datasets")
    .select("*")
    .limit(5)
    .execute()
)

print("Supabase connection successful!")

print(response.data)