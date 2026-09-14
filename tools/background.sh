#!/usr/bin/env bash
# Run experiments in the background, detached from the terminal that started them, so they keep going
# when VS Code, the terminal or an SSH connection is closed. Runs inside the container.
#
#   bash tools/background.sh start <name> <runner arguments...>   start python -m pfexp.run in the background
#   bash tools/background.sh running                              show the background run, if any
#   bash tools/background.sh log                                  follow the output of the latest run
#   bash tools/background.sh stop                                 stop it (finished runs are kept)
#
# One background run at a time, so runs don't compete for the same cores.
# Output is added to .build/logs/<name>.log; the process id of the current run is kept in .build/logs/current.
set -u
cd "$(dirname "$0")/.."

LOGS=.build/logs
CURRENT=$LOGS/current   # two lines: process id, log file

alive() {  # the process exists and has not finished (a finished child of a non-reaping PID 1 stays a zombie)
    local state
    state=$(awk '{print $3}' "/proc/$1/stat" 2>/dev/null) || return 1
    [ -n "$state" ] && [ "$state" != Z ]
}

read_current() {  # sets PID and LOG; fails if there is no background run
    [ -f "$CURRENT" ] || return 1
    { read -r PID; read -r LOG; } < "$CURRENT"
    [ -n "${PID:-}" ]
}

case "${1:-}" in
start)
    name=${2:?usage: background.sh start <name> <runner arguments...>}
    shift 2
    if read_current && alive "$PID"; then
        echo "A background run is still going (process $PID, log $LOG)."
        echo "Wait for it (make running), or stop it first (make stop)."
        exit 1
    fi
    mkdir -p "$LOGS"
    LOG=$LOGS/$name.log
    echo "=== $(date '+%Y-%m-%d %H:%M:%S') python -m pfexp.run $*" >> "$LOG"
    # setsid -f: own session and process group, so closing the terminal does not reach it and stop can signal
    # all workers. Not started with `&`: a script's background commands ignore Ctrl+C, and so would ignore stop.
    rm -f "$CURRENT.pid"
    setsid -f bash -c 'echo $$ > "$0.pid"; exec python -m pfexp.run "$@"' "$CURRENT" "$@" >> "$LOG" 2>&1 < /dev/null
    for _ in $(seq 50); do [ -s "$CURRENT.pid" ] && break; sleep 0.1; done
    PID=$(cat "$CURRENT.pid") || { echo "The run did not start; see $LOG"; exit 1; }
    rm -f "$CURRENT.pid"
    printf '%s\n%s\n' "$PID" "$LOG" > "$CURRENT"
    echo "Started in the background (process $PID). It keeps running when VS Code or the terminal is closed."
    echo "  follow it:  make log        see if it is still going:  make running        stop it:  make stop"
    echo "  log file:   $LOG"
    ;;
running)
    if read_current && alive "$PID"; then
        echo "Running: process $PID for $(ps -o etime= -p "$PID" | tr -d ' '), log $LOG"
        tail -n 3 "$LOG"
    elif read_current; then
        echo "Nothing running. The last background run has finished; its output is in $LOG:"
        tail -n 3 "$LOG"
    else
        echo "Nothing running in the background."
    fi
    ;;
log)
    read_current || { echo "No background run has been started yet."; exit 1; }
    echo "Following $LOG (Ctrl+C stops following, not the run)"
    tail -n 20 -f "$LOG" &
    follow=$!
    trap 'kill $follow 2>/dev/null; exit 0' INT TERM
    while alive "$PID"; do sleep 1; done
    sleep 1
    kill $follow 2>/dev/null
    echo "The run has finished."
    ;;
stop)
    if read_current && alive "$PID"; then
        kill -INT -- "-$PID"   # Ctrl+C for the whole group: the runner and its workers
        for _ in $(seq 30); do alive "$PID" || break; sleep 1; done
        alive "$PID" && kill -TERM -- "-$PID"
        echo "Stopped. Finished runs are kept; start the same experiment again to continue."
    else
        echo "Nothing running in the background."
    fi
    ;;
*)
    sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
    ;;
esac
