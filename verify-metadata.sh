#!/bin/bash
# verify-metadata.sh - Verify repository metadata for GitHub recognition

echo "🔍 Verifying repository metadata..."
echo ""

# Check LICENSE
if [ -f "LICENSE" ]; then
    echo "✅ LICENSE file exists"
    echo "   Size: $(wc -c < LICENSE) bytes"
    echo "   Content preview:"
    head -n 3 LICENSE | sed 's/^/      /'
else
    echo "❌ LICENSE file missing"
fi

echo ""

# Check COPYING
if [ -f "COPYING" ]; then
    echo "✅ COPYING file exists (alternative license reference)"
else
    echo "⚠️  COPYING file missing (optional)"
fi

echo ""

# Check package.json has license
if [ -f "frontend/package.json" ]; then
    if grep -q '"license"' frontend/package.json; then
        echo "✅ frontend/package.json has license field"
    else
        echo "⚠️  frontend/package.json missing license field"
    fi
fi

echo ""

# Check pyproject.toml
if [ -f "pyproject.toml" ]; then
    if grep -q 'license' pyproject.toml; then
        echo "✅ pyproject.toml has license field"
    else
        echo "⚠️  pyproject.toml missing license field"
    fi
fi

echo ""

# Check git tags
echo "📦 Git tags (releases):"
git tag -l | while read tag; do
    echo "   - $tag"
done

echo ""
echo "✨ Verification complete!"
