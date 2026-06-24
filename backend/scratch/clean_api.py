import re

with open("../frontend/src/lib/api.ts", "r") as f:
    content = f.read()

# 1. Update apiFetch signature
content = re.sub(
    r"async function apiFetch<T>\(\s*endpoint: string,\s*options: RequestInit = \{\},\s*useMockOnFail\?: \(\) => T\s*\): Promise<T> \{",
    "async function apiFetch<T>(\n  endpoint: string,\n  options: RequestInit = {}\n): Promise<T> {",
    content
)

# 2. Update apiFetch catch block
content = re.sub(
    r"\} catch \(error\) \{\s*if \(useMockOnFail\) \{\s*console\.warn\(`\[PhishGuard API\] Using mock data for \$\{endpoint\}:`, error\);\s*return useMockOnFail\(\);\s*\}\s*throw error;\s*\}",
    "} catch (error) {\n    throw error;\n  }",
    content
)

# 3. Update apiFetchFormData signature
content = re.sub(
    r"async function apiFetchFormData<T>\(\s*endpoint: string,\s*formData: FormData,\s*useMockOnFail\?: \(\) => T\s*\): Promise<T> \{",
    "async function apiFetchFormData<T>(\n  endpoint: string,\n  formData: FormData\n): Promise<T> {",
    content
)

# 4. Update apiFetchFormData catch block
content = re.sub(
    r"\} catch \(error\) \{\s*if \(useMockOnFail\) \{\s*console\.warn\(`\[PhishGuard API\] Using mock data for \$\{endpoint\}:`, error\);\s*return useMockOnFail\(\);\s*\}\s*throw error;\s*\}",
    "} catch (error) {\n    throw error;\n  }",
    content
)

# 5. Remove mock data imports
content = re.sub(
    r"import \{\s*mockDashboardStats.*?} from '\./mock-data';",
    "",
    content,
    flags=re.DOTALL
)

# 6. We also need to remove the mock fallback arguments from the actual calls.
# e.g., return apiFetch('/api/v1/dashboard/stats', {}, () => mockDashboardStats);
# We can use a regex to replace `, () => .*?\);` with `);` but some span multiple lines.
# Instead, since we removed the signature parameter, TypeScript will complain if we leave them, but maybe we just leave them and ignore TS errors? No, Next.js build will fail.
# Let's do a more robust regex or just write a quick AST parser in Python? No, Regex is fine for these.

with open("../frontend/src/lib/api.ts", "w") as f:
    f.write(content)

print("Pass 1 complete")
