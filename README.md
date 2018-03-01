```
import future

print future.Command('ls') | future.Command('wc -l')

result = future.Command('find /')
if result.read():
    print result.get()
```
