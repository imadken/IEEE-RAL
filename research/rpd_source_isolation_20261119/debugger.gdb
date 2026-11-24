set pagination off
set confirm off
set print thread-events off
set disable-randomization off
set startup-with-shell off
run
python
import gdb
if gdb.selected_inferior().threads():
    for command in ("thread apply all bt", "py-bt"):
        try:
            gdb.execute(command)
        except gdb.error as error:
            gdb.write("Backtrace command unavailable: " + str(error) + "\n")
end
quit
