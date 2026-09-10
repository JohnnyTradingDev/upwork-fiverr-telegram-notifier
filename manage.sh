#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

case "$1" in
  start)
    systemctl --user start upwork-notifier
    echo "Started upwork-notifier service."
    ;;
  stop)
    systemctl --user stop upwork-notifier
    echo "Stopped upwork-notifier service."
    ;;
  restart)
    systemctl --user restart upwork-notifier
    echo "Restarted upwork-notifier service."
    ;;
  status)
    systemctl --user status upwork-notifier
    ;;
  logs)
    journalctl --user -u upwork-notifier -f -o cat
    ;;
  test)
    "$DIR/venv/bin/python3" "$DIR/test_telegram.py"
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs|test}"
    exit 1
    ;;
esac
