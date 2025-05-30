#!/bin/bash

# Stop development environment script

echo "🛑 Stopping Medical Terminology Mapper Development Environment..."

# Get the directory where the script is located (now in root)
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to project directory
cd "$PROJECT_DIR"

# Function to close browser tabs on macOS
close_browser_tabs_macos() {
    osascript <<EOF 2>/dev/null
    tell application "Safari"
        if it is running then
            close (every tab of every window whose URL contains "localhost:3000")
            close (every tab of every window whose URL contains "localhost:8000")
        end if
    end tell
    
    tell application "Google Chrome"
        if it is running then
            set windowList to every window
            repeat with aWindow in windowList
                set tabList to every tab of aWindow
                repeat with atab in tabList
                    if (URL of atab contains "localhost:3000") or (URL of atab contains "localhost:8000") then
                        close atab
                    end if
                end repeat
            end repeat
        end if
    end tell
    
    tell application "Firefox"
        if it is running then
            # Firefox doesn't have good AppleScript support for closing specific tabs
            # This will just notify the user
            display notification "Please close Firefox tabs manually" with title "Medical Terminology Mapper"
        end if
    end tell
EOF
}

# Function to close browser tabs on Linux
close_browser_tabs_linux() {
    # This is more difficult on Linux as there's no standard way
    # We'll use xdotool if available
    if command -v xdotool > /dev/null; then
        echo "📌 Attempting to close browser tabs..."
        # Find windows with localhost in title
        xdotool search --name "localhost" windowclose 2>/dev/null || true
    else
        echo "💡 Tip: Install xdotool to automatically close browser tabs"
    fi
}

# Detect OS and close browser tabs
echo "🌐 Closing browser tabs..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    close_browser_tabs_macos
    echo "✅ Browser tabs closed (Safari, Chrome)"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    close_browser_tabs_linux
fi

# Stop and remove containers
echo "🐳 Stopping Docker containers..."
docker-compose down --remove-orphans

# Remove volumes if requested
if [ "$1" == "--clean" ]; then
    echo "🧹 Removing volumes..."
    docker-compose down -v
    echo "✅ Volumes removed"
fi

# Show container status
echo ""
echo "📊 Container status:"
docker-compose ps

echo ""
echo "✅ All services stopped."
echo ""
echo "💡 Tips:"
echo "  - To start again: ./start-dev.sh"
echo "  - To clean everything (including volumes): ./stop-dev.sh --clean"
echo "  - To remove all Docker images: docker-compose down --rmi all"