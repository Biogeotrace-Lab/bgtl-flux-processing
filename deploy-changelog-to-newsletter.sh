set -e

markdown CHANGELOG.md | ssh bgtl-ec-tower-server "cat > services/bgtl-fluxy-newsletter/changelog.html"

