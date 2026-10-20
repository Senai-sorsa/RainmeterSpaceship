What happens if volume is off when wake training occurs?

I should be able to type in the chat thing which he uses to talk to me while on mute  
The training can get interrupted? Thats not supposed to happen  
Whenever i say “nevermind” he says “okay nevermind”, he should say nothing  
Instead of having the training work like this, could recordings from a online generator be better? Dont we need to do this for “Hey clover” anyways? tell me why or why not?

Just  “JARVIS” shouldn’t work as a wake word but it currently does

GPU load is consistently at 80% \- and it goes down when rainmeter is turned off. Why is this? Try to reduce this and address this issue.

After stop it should be on listening mode for one second (to detect if i say anything directly after stop) and treat this like a follow up

Stop works  
And stop sign doesn’t break anything  
But currently its taking way longer to respond

C.L.O.V.E.R \- doesn’t change when i select jarvis

After recalling memory it can directly skip follow up mode  
Basically nothing but direct commands should skip follow up mode (but even commands should listen for an undo for a couple seconds)  
Adding a removing a timer works well

Most things are fast but the chat takes a while   
Here is the log  
2026-10-17 23:31:55  started (C:\\Users\\Senai\\Rainmeter\\Skins\\Spaceship\\@Resources), Python 3.12.10  
2026-10-17 23:31:58  wake word ready \- say 'Hey Jarvis'  
2026-10-17 23:32:04  kokoro loaded (kokoro-v1.0.onnx, voices-v1.0.bin), on the GPU  
2026-10-17 23:32:04  kokoro speaking with voice bm\_lewis  
2026-10-17 23:32:04  wake: your checks: hey\_jarvis, hey, jarvis  
2026-10-17 23:32:06  whisper small.en on GPU  
2026-10-17 23:32:07  meaning match: ready  
2026-10-17 23:33:02  wake word heard (0.99, HV)  
2026-10-17 23:33:03  timing: click \-\> listening 0.95s  
2026-10-17 23:33:05  timing: listening \-\> end of speech 2.84s  
2026-10-17 23:33:06  timing: end of speech \-\> text 0.54s  
2026-10-17 23:33:06  you: 1 words  
2026-10-17 23:33:06  control: ended by you  
2026-10-17 23:33:06  route: control via rule, total 0.54s \-\> said  
2026-10-17 23:33:58  wake: best 0.99 this minute  
2026-10-17 23:36:34  wake word heard (0.33, HV)  
2026-10-17 23:36:35  timing: click \-\> listening 0.93s  
2026-10-17 23:36:38  timing: listening \-\> end of speech 2.67s  
2026-10-17 23:36:38  timing: end of speech \-\> text 0.32s  
2026-10-17 23:36:38  you: 5 words  
2026-10-17 23:36:38  action: volume ('step', \-10)  
2026-10-17 23:36:39  timing: reply start \-\> first sentence 0.00s, its voice 0.12s  
2026-10-17 23:36:39  timing: reply start \-\> first audio 0.13s  
2026-10-17 23:36:40  stop words ready  
2026-10-17 23:36:41  route: command.act volume via rule, total 2.66s \-\> said  
2026-10-17 23:36:41  timing: click \-\> listening 0.39s  
2026-10-17 23:36:48  timing: listening \-\> end of speech 6.45s  
2026-10-17 23:36:48  timing: end of speech \-\> text 0.30s  
2026-10-17 23:36:48  you: 10 words  
2026-10-17 23:36:48  topic memory: 2 topic(s) recalled  
2026-10-17 23:36:48  timing: end of speech \-\> reply start 0.36s  
2026-10-17 23:36:52  timing: reply start \-\> first sentence 4.28s, its voice 0.25s  
2026-10-17 23:36:52  timing: reply start \-\> first audio 4.54s  
2026-10-17 23:36:58  wake: best 0.33 this minute  
2026-10-17 23:37:00  timing: end of speech \-\> reply done 12.76s (llama3.1:8b)  
2026-10-17 23:37:00  clover: 101 characters  
2026-10-17 23:37:00  route: chat.chat via model, total 12.76s \-\> answered  
2026-10-17 23:37:01  timing: click \-\> listening 0.42s  
2026-10-17 23:37:07  timing: listening \-\> end of speech 5.81s  
2026-10-17 23:37:07  timing: end of speech \-\> text 0.26s  
2026-10-17 23:37:07  you: 7 words  
2026-10-17 23:37:07  topic memory: 2 topic(s) recalled  
2026-10-17 23:37:07  timing: end of speech \-\> reply start 0.32s  
2026-10-17 23:37:07  timing: reply start \-\> first sentence 0.37s, its voice 0.21s  
2026-10-17 23:37:07  timing: reply start \-\> first audio 0.58s  
2026-10-17 23:37:12  timing: end of speech \-\> reply done 5.27s (llama3.1:8b)  
2026-10-17 23:37:12  clover: 43 characters  
2026-10-17 23:37:12  route: chat.chat via model, total 5.28s \-\> answered  
2026-10-17 23:37:12  timing: click \-\> listening 0.43s  
2026-10-17 23:37:18  timing: listening \-\> end of speech 5.43s  
2026-10-17 23:37:18  timing: end of speech \-\> text 0.27s  
2026-10-17 23:37:18  you: 2 words  
2026-10-17 23:37:18  timing: reply start \-\> first sentence 0.00s, its voice 0.08s  
2026-10-17 23:37:18  timing: reply start \-\> first audio 0.08s  
2026-10-17 23:37:19  route: courtesy via rule, total 1.71s \-\> said  
2026-10-17 23:37:20  timing: click \-\> listening 0.40s  
2026-10-17 23:37:25  timing: listening \-\> end of speech 5.31s  
2026-10-17 23:37:25  timing: end of speech \-\> text 0.30s  
2026-10-17 23:37:25  you: 5 words  
2026-10-17 23:37:25  action: volume ('set', 20\)  
2026-10-17 23:37:26  timing: reply start \-\> first sentence 0.00s, its voice 0.15s  
2026-10-17 23:37:26  timing: reply start \-\> first audio 0.15s  
2026-10-17 23:37:28  route: command.act volume via rule, total 2.67s \-\> said  
2026-10-17 23:37:28  timing: click \-\> listening 0.44s  
2026-10-17 23:37:39  timing: listening \-\> end of speech 11.10s  
2026-10-17 23:37:40  timing: end of speech \-\> text 0.37s  
2026-10-17 23:37:40  you: 16 words  
2026-10-17 23:37:40  interpreter: 1 commands, 0.8s  
2026-10-17 23:37:40  action: volume ('set', 20\)  
2026-10-17 23:37:41  timing: reply start \-\> first sentence 0.00s, its voice 0.09s  
2026-10-17 23:37:41  timing: reply start \-\> first audio 0.09s  
2026-10-17 23:37:43  route: command.act volume via ai-reread, total 4.12s \-\> said  
2026-10-17 23:37:44  timing: click \-\> listening 0.43s  
2026-10-17 23:37:55  timing: listening \-\> end of speech 10.86s  
2026-10-17 23:37:55  timing: end of speech \-\> text 0.34s  
2026-10-17 23:37:55  you: 10 words  
2026-10-17 23:37:55  topic memory: 2 topic(s) recalled  
2026-10-17 23:37:55  timing: end of speech \-\> reply start 0.38s  
2026-10-17 23:37:56  timing: reply start \-\> first sentence 0.40s, its voice 0.38s  
2026-10-17 23:37:56  timing: reply start \-\> first audio 0.78s  
2026-10-17 23:38:03  timing: end of speech \-\> reply done 8.03s (llama3.1:8b)  
2026-10-17 23:38:03  clover: 84 characters  
2026-10-17 23:38:03  route: chat.chat via model, total 8.03s \-\> answered  
2026-10-17 23:38:03  timing: click \-\> listening 0.42s  
2026-10-17 23:38:08  timing: listening \-\> end of speech 5.33s  
2026-10-17 23:38:09  timing: end of speech \-\> text 0.28s  
2026-10-17 23:38:09  you: 4 words  
2026-10-17 23:38:09  control: ended by you  
2026-10-17 23:38:09  route: control via rule, total 0.28s \-\> said  
2026-10-17 23:38:15  wake word heard (0.64, HV)  
2026-10-17 23:38:16  timing: click \-\> listening 0.89s  
2026-10-17 23:38:19  timing: listening \-\> end of speech 3.75s  
2026-10-17 23:38:19  timing: end of speech \-\> text 0.11s  
2026-10-17 23:38:19  you: 3 words  
2026-10-17 23:38:19  action: volume ('set', 50\)  
2026-10-17 23:38:20  timing: reply start \-\> first sentence 0.00s, its voice 0.10s  
2026-10-17 23:38:20  timing: reply start \-\> first audio 0.10s  
2026-10-17 23:38:22  route: command.act volume via rule, total 2.46s \-\> said  
2026-10-17 23:38:22  timing: click \-\> listening 0.43s  
2026-10-17 23:38:36  wake word heard (0.34, HV)  
2026-10-17 23:38:37  timing: click \-\> listening 0.92s  
2026-10-17 23:38:42  timing: listening \-\> end of speech 5.00s  
2026-10-17 23:38:42  timing: end of speech \-\> text 0.34s  
2026-10-17 23:38:42  you: 10 words  
2026-10-17 23:38:42  topic memory: 3 exchange(s) filed, 4 topics  
2026-10-17 23:38:43  timing: end of speech \-\> reply start 0.47s  
2026-10-17 23:38:46  timing: reply start \-\> first sentence 3.60s, its voice 0.28s  
2026-10-17 23:38:46  timing: reply start \-\> first audio 3.88s  
2026-10-17 23:38:52  timing: end of speech \-\> reply done 10.11s (llama3.1:8b)  
2026-10-17 23:38:52  clover: 67 characters  
2026-10-17 23:38:52  route: chat.chat via model, total 10.11s \-\> answered  
2026-10-17 23:38:53  timing: click \-\> listening 0.41s  
2026-10-17 23:38:58  timing: listening \-\> end of speech 5.21s  
2026-10-17 23:38:58  timing: end of speech \-\> text 0.33s  
2026-10-17 23:38:58  you: 4 words  
2026-10-17 23:38:58  ear: unsure \- stayed quiet  
2026-10-17 23:38:58  route: ear via rule, total 0.34s \-\> not for me \- quiet  
2026-10-17 23:38:58  wake: best 0.64 this minute  
2026-10-17 23:39:03  wake word heard (0.79, HV)  
2026-10-17 23:39:04  timing: click \-\> listening 0.90s  
2026-10-17 23:39:11  timing: listening \-\> end of speech 7.59s  
2026-10-17 23:39:12  timing: end of speech \-\> text 0.28s  
2026-10-17 23:39:12  you: 13 words  
2026-10-17 23:39:12  timing: end of speech \-\> reply start 0.33s  
2026-10-17 23:39:16  timing: reply start \-\> first sentence 3.97s, its voice 0.24s  
2026-10-17 23:39:16  timing: reply start \-\> first audio 4.21s  
2026-10-17 23:39:23  timing: end of speech \-\> reply done 11.34s (llama3.1:8b)  
2026-10-17 23:39:23  clover: 69 characters  
2026-10-17 23:39:23  route: chat.chat via model, total 11.34s \-\> answered  
2026-10-17 23:39:23  timing: click \-\> listening 0.42s  
2026-10-17 23:39:30  timing: listening \-\> end of speech 7.22s  
2026-10-17 23:39:31  timing: end of speech \-\> text 0.27s  
2026-10-17 23:39:31  you: 6 words  
2026-10-17 23:39:31  topic memory: 2 exchange(s) filed, 4 topics  
2026-10-17 23:39:31  topic memory: 2 topic(s) recalled  
2026-10-17 23:39:31  timing: end of speech \-\> reply start 0.34s  
2026-10-17 23:39:31  timing: reply start \-\> first sentence 0.23s, its voice 0.13s  
2026-10-17 23:39:31  timing: reply start \-\> first audio 0.37s  
2026-10-17 23:39:34  timing: end of speech \-\> reply done 3.75s (llama3.1:8b)  
2026-10-17 23:39:34  clover: 30 characters  
2026-10-17 23:39:34  route: chat.chat via model, total 3.75s \-\> answered  
2026-10-17 23:39:34  timing: click \-\> listening 0.39s  
2026-10-17 23:39:40  timing: listening \-\> end of speech 5.18s  
2026-10-17 23:39:40  timing: end of speech \-\> text 0.35s  
2026-10-17 23:39:40  you: 7 words  
2026-10-17 23:39:40  timing: end of speech \-\> reply start 0.38s  
2026-10-17 23:39:40  timing: reply start \-\> first sentence 0.16s, its voice 0.17s  
2026-10-17 23:39:40  timing: reply start \-\> first audio 0.33s  
2026-10-17 23:39:44  timing: end of speech \-\> reply done 4.38s (llama3.1:8b)  
2026-10-17 23:39:44  clover: 39 characters  
2026-10-17 23:39:44  route: chat.chat via model, total 4.38s \-\> answered  
2026-10-17 23:39:44  timing: click \-\> listening 0.42s  
2026-10-17 23:39:50  timing: listening \-\> end of speech 5.52s  
2026-10-17 23:39:50  timing: end of speech \-\> text 0.21s  
2026-10-17 23:39:50  you: 4 words  
2026-10-17 23:39:50  topic memory: 2 topic(s) recalled  
2026-10-17 23:39:50  timing: end of speech \-\> reply start 0.28s  
2026-10-17 23:39:51  timing: reply start \-\> first sentence 0.35s, its voice 0.05s  
2026-10-17 23:39:51  timing: reply start \-\> first audio 0.41s  
2026-10-17 23:39:52  timing: end of speech \-\> reply done 2.12s (llama3.1:8b)  
2026-10-17 23:39:52  clover: 15 characters  
2026-10-17 23:39:52  route: chat.chat via model, total 2.12s \-\> answered  
2026-10-17 23:39:52  timing: click \-\> listening 0.40s  
2026-10-17 23:39:58  timing: listening \-\> end of speech 5.91s  
2026-10-17 23:39:59  timing: end of speech \-\> text 0.25s  
2026-10-17 23:39:59  you: 11 words  
2026-10-17 23:39:59  timing: end of speech \-\> reply start 0.29s  
2026-10-17 23:39:59  timing: reply start \-\> first sentence 0.19s, its voice 0.22s  
2026-10-17 23:39:59  timing: reply start \-\> first audio 0.40s  
2026-10-17 23:39:59  wake: best 0.79 this minute  
2026-10-17 23:40:04  timing: end of speech \-\> reply done 5.44s (llama3.1:8b)  
2026-10-17 23:40:04  clover: 47 characters  
2026-10-17 23:40:04  route: chat.chat via model, total 5.44s \-\> answered  
2026-10-17 23:40:04  timing: click \-\> listening 0.40s  
2026-10-17 23:40:09  timing: listening \-\> end of speech 4.85s  
2026-10-17 23:40:09  timing: end of speech \-\> text 0.31s  
2026-10-17 23:40:09  you: 7 words  
2026-10-17 23:40:09  topic memory: 2 topic(s) recalled  
2026-10-17 23:40:09  timing: end of speech \-\> reply start 0.35s  
2026-10-17 23:40:10  timing: reply start \-\> first sentence 0.40s, its voice 0.14s  
2026-10-17 23:40:10  timing: reply start \-\> first audio 0.54s  
2026-10-17 23:40:13  timing: end of speech \-\> reply done 3.84s (llama3.1:8b)  
2026-10-17 23:40:13  clover: 27 characters  
2026-10-17 23:40:13  route: chat.chat via model, total 3.85s \-\> answered  
2026-10-17 23:40:13  timing: click \-\> listening 0.42s  
2026-10-17 23:40:22  timing: listening \-\> end of speech 8.48s  
2026-10-17 23:40:22  timing: end of speech \-\> text 0.41s  
2026-10-17 23:40:22  you: 19 words  
2026-10-17 23:40:22  timing: end of speech \-\> reply start 0.49s  
2026-10-17 23:40:23  timing: reply start \-\> first sentence 0.28s, its voice 0.15s  
2026-10-17 23:40:23  timing: reply start \-\> first audio 0.44s  
2026-10-17 23:40:26  timing: end of speech \-\> reply done 4.19s (llama3.1:8b)  
2026-10-17 23:40:26  clover: 39 characters  
2026-10-17 23:40:26  route: chat.chat via model, total 4.19s \-\> answered  
2026-10-17 23:40:26  timing: click \-\> listening 0.42s  
2026-10-17 23:40:35  timing: listening \-\> end of speech 8.85s  
2026-10-17 23:40:36  timing: end of speech \-\> text 0.35s  
2026-10-17 23:40:36  you: 15 words  
2026-10-17 23:40:36  topic memory: 6 exchange(s) filed, 7 topics  
2026-10-17 23:40:36  timing: end of speech \-\> reply start 0.40s  
2026-10-17 23:40:36  timing: reply start \-\> first sentence 0.13s, its voice 0.20s  
2026-10-17 23:40:36  timing: reply start \-\> first audio 0.33s  
2026-10-17 23:40:41  timing: end of speech \-\> reply done 5.91s (llama3.1:8b)  
2026-10-17 23:40:41  clover: 63 characters  
2026-10-17 23:40:41  route: chat.chat via model, total 5.91s \-\> answered  
2026-10-17 23:40:42  timing: click \-\> listening 0.43s  
2026-10-17 23:40:47  timing: listening \-\> end of speech 5.82s  
2026-10-17 23:40:48  timing: end of speech \-\> text 0.36s  
2026-10-17 23:40:48  you: 11 words  
2026-10-17 23:40:48  timing: end of speech \-\> reply start 0.40s  
2026-10-17 23:40:48  timing: reply start \-\> first sentence 0.35s, its voice 0.32s  
2026-10-17 23:40:48  timing: reply start \-\> first audio 0.67s  
2026-10-17 23:40:59  timing: end of speech \-\> reply done 12.01s (llama3.1:8b)  
2026-10-17 23:40:59  clover: 162 characters  
2026-10-17 23:40:59  route: chat.chat via model, total 12.01s \-\> answered  
2026-10-17 23:41:00  timing: click \-\> listening 0.43s  
2026-10-17 23:41:05  timing: listening \-\> end of speech 5.43s  
2026-10-17 23:41:06  timing: end of speech \-\> text 0.32s  
2026-10-17 23:41:06  you: 11 words  
2026-10-17 23:41:06  interpreter: no command  
2026-10-17 23:41:06  timing: end of speech \-\> reply start 0.72s  
2026-10-17 23:41:06  timing: reply start \-\> first sentence 0.24s, its voice 0.14s  
2026-10-17 23:41:07  timing: reply start \-\> first audio 1.03s  
2026-10-17 23:41:10  timing: end of speech \-\> reply done 4.74s (llama3.1:8b)  
2026-10-17 23:41:10  clover: 29 characters  
2026-10-17 23:41:10  route: chat.chat via model, total 4.74s \-\> answered  
2026-10-17 23:41:10  timing: click \-\> listening 0.44s  
2026-10-17 23:41:14  timing: listening \-\> end of speech 3.74s  
2026-10-17 23:41:15  timing: end of speech \-\> text 0.28s  
2026-10-17 23:41:15  you: 4 words  
2026-10-17 23:41:15  interpreter: fallback (not what was said)  
2026-10-17 23:41:15  topic memory: 1 topic(s) recalled  
2026-10-17 23:41:15  timing: end of speech \-\> reply start 0.89s  
2026-10-17 23:41:15  timing: reply start \-\> first sentence 0.28s, its voice 0.11s  
2026-10-17 23:41:16  timing: reply start \-\> first audio 0.82s  
2026-10-17 23:41:18  timing: end of speech \-\> reply done 3.85s (llama3.1:8b)  
2026-10-17 23:41:18  clover: 26 characters  
2026-10-17 23:41:18  route: chat.chat via model, total 3.85s \-\> answered  
2026-10-17 23:41:19  timing: click \-\> listening 0.42s  
2026-10-17 23:42:43  kokoro speaking with voice default  
2026-10-17 23:42:44  timing: click \-\> listening 0.92s  
2026-10-17 23:42:48  timing: listening \-\> end of speech 4.02s  
2026-10-17 23:42:48  timing: end of speech \-\> text 0.13s  
2026-10-17 23:42:48  you: 6 words  
2026-10-17 23:42:48  topic memory: 2 topic(s) recalled  
2026-10-17 23:42:48  timing: end of speech \-\> reply start 0.17s  
2026-10-17 23:42:52  timing: reply start \-\> first sentence 3.63s, its voice 0.11s  
2026-10-17 23:42:52  timing: reply start \-\> first audio 3.74s  
2026-10-17 23:42:54  timing: end of speech \-\> reply done 6.14s (llama3.1:8b)  
2026-10-17 23:42:54  clover: 30 characters  
2026-10-17 23:42:54  route: chat.chat via model, total 6.14s \-\> answered  
2026-10-17 23:42:54  timing: click \-\> listening 0.39s  
2026-10-17 23:43:01  timing: listening \-\> end of speech 6.89s  
2026-10-17 23:43:01  timing: end of speech \-\> text 0.35s  
2026-10-17 23:43:01  you: 11 words  
2026-10-17 23:43:01  topic memory: 1 topic(s) recalled  
2026-10-17 23:43:01  timing: end of speech \-\> reply start 0.40s  
2026-10-17 23:43:02  timing: reply start \-\> first sentence 0.46s, its voice 0.13s  
2026-10-17 23:43:02  timing: reply start \-\> first audio 0.60s  
2026-10-17 23:43:05  timing: end of speech \-\> reply done 4.07s (llama3.1:8b)  
2026-10-17 23:43:05  clover: 30 characters  
2026-10-17 23:43:05  route: chat.chat via model, total 4.08s \-\> answered  
2026-10-17 23:43:06  timing: click \-\> listening 0.42s  
2026-10-17 23:43:10  timing: listening \-\> end of speech 4.04s  
2026-10-17 23:43:10  timing: end of speech \-\> text 0.32s  
2026-10-17 23:43:10  you: 5 words  
2026-10-17 23:43:10  topic memory: 1 topic(s) recalled  
2026-10-17 23:43:10  timing: end of speech \-\> reply start 0.36s  
2026-10-17 23:43:10  timing: reply start \-\> first sentence 0.16s, its voice 0.17s  
2026-10-17 23:43:10  timing: reply start \-\> first audio 0.33s  
2026-10-17 23:43:14  timing: end of speech \-\> reply done 4.26s (llama3.1:8b)  
2026-10-17 23:43:14  clover: 39 characters  
2026-10-17 23:43:14  route: chat.chat via model, total 4.26s \-\> answered  
2026-10-17 23:43:14  timing: click \-\> listening 0.40s  
2026-10-17 23:43:18  timing: listening \-\> end of speech 4.26s  
2026-10-17 23:43:19  timing: end of speech \-\> text 0.25s  
2026-10-17 23:43:19  you: 4 words  
2026-10-17 23:43:19  timing: reply start \-\> first sentence 0.00s, its voice 0.09s  
2026-10-17 23:43:19  timing: reply start \-\> first audio 0.10s  
2026-10-17 23:43:21  topic memory: 7 exchange(s) filed, 7 topics  
2026-10-17 23:43:21  route: command.say via rule, total 2.30s \-\> said  
2026-10-17 23:44:06  wake word heard (0.41, HV)  
2026-10-17 23:44:07  timing: click \-\> listening 0.89s  
2026-10-17 23:44:13  timing: listening \-\> end of speech 6.48s  
2026-10-17 23:44:13  timing: end of speech \-\> text 0.13s  
2026-10-17 23:44:13  you: 6 words  
2026-10-17 23:44:13  topic memory: 2 topic(s) recalled  
2026-10-17 23:44:13  timing: end of speech \-\> reply start 0.19s  
2026-10-17 23:44:17  timing: reply start \-\> first sentence 3.62s, its voice 0.14s  
2026-10-17 23:44:17  timing: reply start \-\> first audio 3.76s  
2026-10-17 23:44:20  stop word heard (quiet)  
2026-10-17 23:44:20  stop: stop word  
2026-10-17 23:44:20  timing: end of speech \-\> reply done 6.63s (llama3.1:8b)  
2026-10-17 23:44:20  clover: 30 characters  
2026-10-17 23:44:20  route: chat.chat via model, total 6.64s \-\> stopped  
2026-10-17 23:44:32  wake word heard (0.41, HV)  
2026-10-17 23:44:33  timing: click \-\> listening 0.90s  
2026-10-17 23:44:36  timing: listening \-\> end of speech 3.18s  
2026-10-17 23:44:36  timing: end of speech \-\> text 0.10s  
2026-10-17 23:44:36  you: 3 words  
2026-10-17 23:44:36  topic memory: 1 topic(s) recalled  
2026-10-17 23:44:36  timing: end of speech \-\> reply start 0.15s  
2026-10-17 23:44:40  timing: reply start \-\> first sentence 3.56s, its voice 0.10s  
2026-10-17 23:44:40  timing: reply start \-\> first audio 3.67s  
2026-10-17 23:44:42  timing: end of speech \-\> reply done 5.95s (llama3.1:8b)  
2026-10-17 23:44:42  clover: 23 characters  
2026-10-17 23:44:42  route: chat.chat via model, total 5.95s \-\> answered  
2026-10-17 23:44:42  timing: click \-\> listening 0.40s  
2026-10-17 23:44:46  timing: listening \-\> end of speech 3.86s  
2026-10-17 23:44:46  timing: end of speech \-\> text 0.10s  
2026-10-17 23:44:46  you: 2 words  
2026-10-17 23:44:46  control: ended by you  
2026-10-17 23:44:46  route: control via rule, total 0.10s \-\> said  
2026-10-17 23:45:02  wake: best 0.41 this minute  
2026-10-17 23:45:29  wake word heard (0.94, HV)  
2026-10-17 23:45:30  timing: click \-\> listening 0.94s  
2026-10-17 23:45:33  timing: listening \-\> end of speech 3.52s  
2026-10-17 23:45:33  timing: end of speech \-\> text 0.14s  
2026-10-17 23:45:33  you: 7 words  
2026-10-17 23:45:33  topic memory: 2 exchange(s) filed, 7 topics  
2026-10-17 23:45:33  timing: end of speech \-\> reply start 0.21s  
2026-10-17 23:45:37  timing: reply start \-\> first sentence 3.57s, its voice 0.15s  
2026-10-17 23:45:37  timing: reply start \-\> first audio 3.72s  
2026-10-17 23:45:40  timing: end of speech \-\> reply done 7.21s (llama3.1:8b)  
2026-10-17 23:45:40  clover: 39 characters  
2026-10-17 23:45:40  route: chat.chat via model, total 7.21s \-\> answered  
2026-10-17 23:45:41  timing: click \-\> listening 0.40s  
2026-10-17 23:45:50  timing: listening \-\> end of speech 9.24s  
2026-10-17 23:45:50  timing: end of speech \-\> text 0.27s  
2026-10-17 23:45:50  you: 15 words  
2026-10-17 23:45:50  ear: started late without his name \- dropped  
2026-10-17 23:45:50  route: ear via rule, total 0.27s \-\> late, no name \- dropped  
2026-10-17 23:45:54  wake word heard (0.99, HV)  
2026-10-17 23:45:55  timing: click \-\> listening 0.91s  
2026-10-17 23:46:00  timing: listening \-\> end of speech 4.49s  
2026-10-17 23:46:00  timing: end of speech \-\> text 0.13s  
2026-10-17 23:46:00  you: 7 words  
2026-10-17 23:46:00  topic memory: 1 topic(s) recalled  
2026-10-17 23:46:00  timing: end of speech \-\> reply start 0.17s  
2026-10-17 23:46:04  timing: reply start \-\> first sentence 3.59s, its voice 0.24s  
2026-10-17 23:46:04  timing: reply start \-\> first audio 3.83s  
2026-10-17 23:46:04  wake: best 0.99 this minute  
2026-10-17 23:46:09  timing: end of speech \-\> reply done 9.38s (llama3.1:8b)  
2026-10-17 23:46:09  clover: 74 characters  
2026-10-17 23:46:09  route: chat.chat via model, total 9.38s \-\> answered  
2026-10-17 23:46:09  timing: click \-\> listening 0.42s  
2026-10-17 23:46:15  timing: listening \-\> end of speech 5.03s  
2026-10-17 23:46:15  timing: end of speech \-\> text 0.26s  
2026-10-17 23:46:15  you: 6 words  
2026-10-17 23:46:15  topic memory: 2 exchange(s) filed, 7 topics  
2026-10-17 23:46:15  timing: end of speech \-\> reply start 0.32s  
2026-10-17 23:46:15  timing: reply start \-\> first sentence 0.16s, its voice 0.25s  
2026-10-17 23:46:15  timing: reply start \-\> first audio 0.41s  
2026-10-17 23:46:20  timing: end of speech \-\> reply done 5.46s (llama3.1:8b)  
2026-10-17 23:46:20  clover: 65 characters  
2026-10-17 23:46:20  route: chat.chat via model, total 5.46s \-\> answered  
2026-10-17 23:46:20  timing: click \-\> listening 0.41s  
2026-10-17 23:46:24  timing: listening \-\> end of speech 3.72s  
2026-10-17 23:46:24  timing: end of speech \-\> text 0.25s  
2026-10-17 23:46:24  you: 5 words  
2026-10-17 23:46:24  timing: end of speech \-\> reply start 0.30s  
2026-10-17 23:46:25  timing: reply start \-\> first sentence 0.33s, its voice 0.13s  
2026-10-17 23:46:25  timing: reply start \-\> first audio 0.46s  
2026-10-17 23:46:28  timing: end of speech \-\> reply done 3.76s (llama3.1:8b)  
2026-10-17 23:46:28  clover: 29 characters  
2026-10-17 23:46:28  route: chat.chat via model, total 3.76s \-\> answered  
2026-10-17 23:46:28  timing: click \-\> listening 0.43s  
2026-10-17 23:46:33  timing: listening \-\> end of speech 4.79s  
2026-10-17 23:46:33  timing: end of speech \-\> text 0.27s  
2026-10-17 23:46:33  you: 7 words  
2026-10-17 23:46:33  timing: end of speech \-\> reply start 0.33s  
2026-10-17 23:46:34  timing: reply start \-\> first sentence 0.32s, its voice 0.10s  
2026-10-17 23:46:34  timing: reply start \-\> first audio 0.42s  
2026-10-17 23:46:36  timing: end of speech \-\> reply done 2.80s (llama3.1:8b)  
2026-10-17 23:46:36  clover: 24 characters  
2026-10-17 23:46:36  route: chat.chat via model, total 2.81s \-\> answered  
2026-10-17 23:46:36  timing: click \-\> listening 0.43s  
2026-10-17 23:48:44  timing: click \-\> listening 0.90s  
2026-10-17 23:48:49  timing: listening \-\> end of speech 5.25s  
2026-10-17 23:48:49  timing: end of speech \-\> text 0.15s  
2026-10-17 23:48:49  you: 9 words  
2026-10-17 23:48:49  topic memory: 3 exchange(s) filed, 7 topics  
2026-10-17 23:48:49  timing: end of speech \-\> reply start 0.24s  
2026-10-17 23:48:53  timing: reply start \-\> first sentence 3.61s, its voice 0.32s  
2026-10-17 23:48:53  timing: reply start \-\> first audio 3.93s  
2026-10-17 23:49:00  timing: end of speech \-\> reply done 10.46s (llama3.1:8b)  
2026-10-17 23:49:00  clover: 63 characters  
2026-10-17 23:49:00  route: info.chat via model, total 10.46s \-\> answered  
2026-10-17 23:49:00  timing: click \-\> listening 0.42s  
2026-10-17 23:49:35  timing: click \-\> listening 0.93s  
2026-10-17 23:49:45  timing: click \-\> listening 0.93s  
2026-10-17 23:50:10  timing: listening \-\> end of speech 25.08s  
2026-10-17 23:50:11  timing: end of speech \-\> text 0.99s  
2026-10-17 23:50:11  you: 77 words  
2026-10-17 23:50:11  topic memory: 1 topic(s) recalled  
2026-10-17 23:50:11  timing: end of speech \-\> reply start 1.02s  
2026-10-17 23:50:15  timing: reply start \-\> first sentence 3.69s, its voice 0.13s  
2026-10-17 23:50:15  timing: reply start \-\> first audio 3.82s  
2026-10-17 23:50:18  timing: end of speech \-\> reply done 7.85s (llama3.1:8b)  
2026-10-17 23:50:18  clover: 29 characters  
2026-10-17 23:50:18  route: chat.chat via model, total 7.85s \-\> answered  
2026-10-17 23:50:18  timing: click \-\> listening 0.39s  
2026-10-17 23:50:30  timing: listening \-\> end of speech 12.12s  
2026-10-17 23:50:30  timing: end of speech \-\> text 0.17s  
2026-10-17 23:50:30  you: 2 words  
2026-10-17 23:50:30  ear: started late without his name \- dropped  
2026-10-17 23:50:30  route: ear via rule, total 0.17s \-\> late, no name \- dropped  
2026-10-17 23:50:36  wake word heard (0.04, HJ)  
2026-10-17 23:50:37  timing: click \-\> listening 0.93s  
2026-10-17 23:50:40  timing: listening \-\> end of speech 3.25s  
2026-10-17 23:50:40  timing: end of speech \-\> text 0.10s  
2026-10-17 23:50:40  you: 1 words  
2026-10-17 23:50:40  timing: reply start \-\> first sentence 0.00s, its voice 0.09s  
2026-10-17 23:50:40  timing: reply start \-\> first audio 0.09s  
2026-10-17 23:50:42  route: command.say via rule, total 2.09s \-\> said  
2026-10-17 23:50:48  wake word heard (0.42, HV)  
2026-10-17 23:50:49  timing: click \-\> listening 0.90s  
2026-10-17 23:50:51  stop: click  
2026-10-17 23:51:15  wake: best 0.46 this minute  
2026-10-17 23:51:39  Rainmeter closed \- exiting  
2026-10-20 10:30:27  started (C:\\Users\\Senai\\Rainmeter\\Skins\\Spaceship\\@Resources), Python 3.12.10  
2026-10-20 10:30:44  wake word ready \- say 'Hey Jarvis'  
2026-10-20 10:31:04  kokoro loaded (kokoro-v1.0.onnx, voices-v1.0.bin), on the GPU  
2026-10-20 10:31:04  kokoro speaking with voice default  
2026-10-20 10:31:04  wake: your checks: hey\_jarvis, hey, jarvis  
2026-10-20 10:31:07  meaning match: ready  
2026-10-20 10:31:48  whisper medium.en on GPU  
2026-10-20 10:31:54  timing: reply start \-\> first sentence 0.00s, its voice 0.24s  
2026-10-20 10:31:54  timing: reply start \-\> first audio 0.24s  
2026-10-20 10:31:56  stop words ready  
2026-10-20 10:32:24  timing: reply start \-\> first sentence 0.00s, its voice 0.24s  
2026-10-20 10:32:24  timing: reply start \-\> first audio 0.24s  
2026-10-20 10:32:53  timing: reply start \-\> first sentence 0.00s, its voice 0.31s  
2026-10-20 10:32:53  timing: reply start \-\> first audio 0.31s  
2026-10-20 10:33:23  timing: reply start \-\> first sentence 0.00s, its voice 0.38s  
2026-10-20 10:33:23  timing: reply start \-\> first audio 0.39s  
2026-10-20 10:33:27  stop word heard (stop)  
2026-10-20 10:33:27  stop: stop word  
2026-10-20 10:34:17  wake word heard (0.45, HV)  
2026-10-20 10:34:18  timing: click \-\> listening 0.87s  
2026-10-20 10:34:21  timing: listening \-\> end of speech 3.18s  
2026-10-20 10:34:21  timing: end of speech \-\> text 0.56s  
2026-10-20 10:34:21  you: 4 words  
2026-10-20 10:34:22  timing: reply start \-\> first sentence 0.00s, its voice 0.10s  
2026-10-20 10:34:22  timing: reply start \-\> first audio 0.10s  
2026-10-20 10:34:23  route: command.say via rule, total 2.55s \-\> said  
2026-10-20 10:34:54  wake: best 0.45 this minute  
2026-10-20 10:36:05  wake word heard (0.75, HV)  
2026-10-20 10:36:06  timing: click \-\> listening 0.89s  
2026-10-20 10:36:09  timing: listening \-\> end of speech 3.00s  
2026-10-20 10:36:09  timing: end of speech \-\> text 0.41s  
2026-10-20 10:36:09  you: 4 words  
2026-10-20 10:36:09  timing: reply start \-\> first sentence 0.00s, its voice 0.06s  
2026-10-20 10:36:09  timing: reply start \-\> first audio 0.07s  
2026-10-20 10:36:11  route: command.say via rule, total 2.35s \-\> said  
2026-10-20 10:36:20  wake word heard (0.31, HV)  
2026-10-20 10:36:20  timing: click \-\> listening 0.88s  
2026-10-20 10:36:24  timing: listening \-\> end of speech 3.78s  
2026-10-20 10:36:25  timing: end of speech \-\> text 0.32s  
2026-10-20 10:36:25  you: 2 words  
2026-10-20 10:36:25  control: ended by you  
2026-10-20 10:36:25  route: control via rule, total 0.32s \-\> said  
2026-10-20 10:36:30  wake word heard (0.93, HV)  
2026-10-20 10:36:31  timing: click \-\> listening 0.90s  
2026-10-20 10:36:54  wake: best 0.93 this minute  
2026-10-20 10:38:05  wake word heard (0.94, HV)  
2026-10-20 10:38:06  timing: click \-\> listening 0.87s  
2026-10-20 10:38:11  timing: listening \-\> end of speech 4.95s  
2026-10-20 10:38:11  timing: end of speech \-\> text 0.39s  
2026-10-20 10:38:11  you: 6 words  
2026-10-20 10:38:12  timing: end of speech \-\> reply start 0.47s  
2026-10-20 10:38:32  timing: reply start \-\> first sentence 20.31s, its voice 0.28s  
2026-10-20 10:38:32  timing: reply start \-\> first audio 20.60s  
2026-10-20 10:38:47  stop word heard (stop)  
2026-10-20 10:38:47  stop: stop word  
2026-10-20 10:38:47  timing: end of speech \-\> reply done 35.80s (llama3.1:8b)  
2026-10-20 10:38:47  clover: 211 characters  
2026-10-20 10:38:47  route: chat.chat via model, total 35.80s \-\> stopped  
2026-10-20 10:38:54  wake: best 0.94 this minute  
2026-10-20 10:40:02  wake word heard (0.46, HV)  
2026-10-20 10:40:03  timing: click \-\> listening 0.89s  
2026-10-20 10:40:06  timing: listening \-\> end of speech 3.42s  
2026-10-20 10:40:06  timing: end of speech \-\> text 0.26s  
2026-10-20 10:40:06  you: 4 words  
2026-10-20 10:40:06  topic memory: 1 exchange(s) filed, 7 topics  
2026-10-20 10:40:06  topic memory: 1 topic(s) recalled  
2026-10-20 10:40:06  timing: end of speech \-\> reply start 0.32s  
2026-10-20 10:40:13  timing: reply start \-\> first sentence 6.77s, its voice 0.20s  
2026-10-20 10:40:13  timing: reply start \-\> first audio 6.97s  
2026-10-20 10:40:29  timing: end of speech \-\> reply done 23.43s (llama3.2:3b)  
2026-10-20 10:40:29  clover: 230 characters  
2026-10-20 10:40:29  route: chat.chat via model, total 23.43s \-\> answered  
2026-10-20 10:40:30  timing: click \-\> listening 0.42s  
2026-10-20 10:40:45  wake word heard (1.00, HV)  
2026-10-20 10:40:46  timing: click \-\> listening 0.89s  
2026-10-20 10:40:49  timing: listening \-\> end of speech 3.83s  
2026-10-20 10:40:50  timing: end of speech \-\> text 0.48s  
2026-10-20 10:40:50  you: 6 words  
2026-10-20 10:40:50  topic memory: 1 exchange(s) filed, 7 topics  
2026-10-20 10:40:50  timing: end of speech \-\> reply start 0.55s  
2026-10-20 10:40:58  timing: reply start \-\> first sentence 8.16s, its voice 0.18s  
2026-10-20 10:40:58  timing: reply start \-\> first audio 8.34s  
2026-10-20 10:40:58  wake: best 1.00 this minute  
2026-10-20 10:41:03  timing: end of speech \-\> reply done 13.81s (llama3.2:3b)  
2026-10-20 10:41:03  clover: 62 characters  
2026-10-20 10:41:03  route: chat.chat via model, total 13.82s \-\> answered  
2026-10-20 10:41:04  timing: click \-\> listening 0.37s  
2026-10-20 10:41:38  wake word heard (0.41, HV)  
2026-10-20 10:41:39  timing: click \-\> listening 0.88s  
2026-10-20 10:41:42  timing: listening \-\> end of speech 2.93s  
2026-10-20 10:41:42  timing: end of speech \-\> text 0.30s  
2026-10-20 10:41:42  you: 2 words  
2026-10-20 10:41:42  timing: end of speech \-\> reply start 0.35s  
2026-10-20 10:41:52  timing: reply start \-\> first sentence 9.27s, its voice 0.23s  
2026-10-20 10:41:52  timing: reply start \-\> first audio 9.49s  
2026-10-20 10:41:58  timing: end of speech \-\> reply done 15.99s (llama3.2:3b)  
2026-10-20 10:41:58  clover: 77 characters  
2026-10-20 10:41:58  route: chat.chat via model, total 15.99s \-\> answered  
2026-10-20 10:41:58  timing: click \-\> listening 0.38s  
2026-10-20 10:42:08  wake: best 0.41 this minute  
2026-10-20 10:42:09  wake word heard (0.45, HV)  
2026-10-20 10:42:10  timing: click \-\> listening 0.87s  
2026-10-20 10:42:17  timing: listening \-\> end of speech 6.36s  
2026-10-20 10:42:17  timing: end of speech \-\> text 0.41s  
2026-10-20 10:42:17  you: 9 words  
2026-10-20 10:42:17  fact saved (2 stored)  
2026-10-20 10:42:17  timing: reply start \-\> first sentence 0.00s, its voice 0.15s  
2026-10-20 10:42:17  timing: reply start \-\> first audio 0.15s  
2026-10-20 10:42:20  topic memory: 2 exchange(s) filed, 7 topics  
2026-10-20 10:42:20  route: command.memory save via rule, total 3.67s \-\> said  
2026-10-20 10:42:21  timing: click \-\> listening 0.39s  
2026-10-20 10:42:34  timing: listening \-\> end of speech 12.95s  
2026-10-20 10:42:34  timing: end of speech \-\> text 0.43s  
2026-10-20 10:42:34  you: 7 words  
2026-10-20 10:42:34  topic memory: 2 topic(s) recalled  
2026-10-20 10:42:34  timing: end of speech \-\> reply start 0.50s  
2026-10-20 10:42:41  timing: reply start \-\> first sentence 6.78s, its voice 0.25s  
2026-10-20 10:42:41  timing: reply start \-\> first audio 7.03s  
2026-10-20 10:42:55  timing: end of speech \-\> reply done 21.22s (llama3.2:3b)  
2026-10-20 10:42:55  clover: 193 characters  
2026-10-20 10:42:55  fact saved (3 stored)  
2026-10-20 10:42:55  route: chat.chat via model, total 21.22s \-\> answered  
2026-10-20 10:42:55  timing: click \-\> listening 0.40s  
2026-10-20 10:43:02  timing: listening \-\> end of speech 7.08s  
2026-10-20 10:43:03  timing: end of speech \-\> text 0.40s  
2026-10-20 10:43:03  you: 10 words  
2026-10-20 10:43:03  topic memory: 1 exchange(s) filed, 7 topics  
2026-10-20 10:43:03  timing: end of speech \-\> reply start 0.47s  
2026-10-20 10:43:03  timing: reply start \-\> first sentence 0.26s, its voice 0.16s  
2026-10-20 10:43:03  timing: reply start \-\> first audio 0.42s  
2026-10-20 10:43:07  timing: end of speech \-\> reply done 4.71s (llama3.2:3b)  
2026-10-20 10:43:07  clover: 46 characters  
2026-10-20 10:43:07  route: chat.chat via model, total 4.71s \-\> answered  
2026-10-20 10:43:07  timing: click \-\> listening 0.39s  
2026-10-20 10:43:13  timing: listening \-\> end of speech 5.10s  
2026-10-20 10:43:13  timing: end of speech \-\> text 0.36s  
2026-10-20 10:43:13  you: 6 words  
2026-10-20 10:43:13  topic memory: 1 exchange(s) filed, 7 topics  
2026-10-20 10:43:13  topic memory: 2 topic(s) recalled  
2026-10-20 10:43:13  timing: end of speech \-\> reply start 0.44s  
2026-10-20 10:43:13  timing: reply start \-\> first sentence 0.28s, its voice 0.13s  
2026-10-20 10:43:13  timing: reply start \-\> first audio 0.41s  
2026-10-20 10:43:14  wake: best 0.45 this minute  
2026-10-20 10:43:17  timing: end of speech \-\> reply done 4.13s (llama3.2:3b)  
2026-10-20 10:43:17  clover: 36 characters  
2026-10-20 10:43:17  route: chat.chat via model, total 4.13s \-\> answered  
2026-10-20 10:43:17  timing: click \-\> listening 0.39s  
2026-10-20 10:43:52  wake word heard (0.78, HV)  
2026-10-20 10:43:53  timing: click \-\> listening 0.88s  
2026-10-20 10:43:56  timing: listening \-\> end of speech 3.56s  
2026-10-20 10:43:57  timing: end of speech \-\> text 0.39s  
2026-10-20 10:43:57  you: 4 words  
2026-10-20 10:43:57  reminder set (timer, 60s ahead, 1\)  
2026-10-20 10:43:57  timing: reply start \-\> first sentence 0.00s, its voice 0.11s  
2026-10-20 10:43:57  timing: reply start \-\> first audio 0.11s  
2026-10-20 10:43:59  topic memory: 1 exchange(s) filed, 7 topics  
2026-10-20 10:43:59  route: command.remind set via rule, total 2.54s \-\> said  
2026-10-20 10:43:59  timing: click \-\> listening 0.39s  
2026-10-20 10:44:03  timing: listening \-\> end of speech 3.14s  
2026-10-20 10:44:03  timing: end of speech \-\> text 0.19s  
2026-10-20 10:44:03  you: 1 words  
2026-10-20 10:44:03  reminder removed by undo (1)  
2026-10-20 10:44:03  timing: reply start \-\> first sentence 0.00s, its voice 0.09s  
2026-10-20 10:44:03  timing: reply start \-\> first audio 0.09s  
2026-10-20 10:44:05  route: command.undo via rule, total 2.05s \-\> said  
2026-10-20 10:44:05  timing: click \-\> listening 0.37s  
2026-10-20 10:44:15  wake: best 0.78 this minute  
2026-10-20 10:44:17  wake word heard (0.84, HV)  
2026-10-20 10:44:18  timing: click \-\> listening 0.89s  
2026-10-20 10:44:22  timing: listening \-\> end of speech 3.35s  
2026-10-20 10:44:22  timing: end of speech \-\> text 0.42s  
2026-10-20 10:44:22  you: 2 words  
2026-10-20 10:44:22  action: open ('Google Chrome', 'Chrome')  
2026-10-20 10:44:23  timing: reply start \-\> first sentence 0.00s, its voice 0.10s  
2026-10-20 10:44:23  timing: reply start \-\> first audio 0.11s  
2026-10-20 10:44:24  route: command.act open via rule, total 2.69s \-\> said  
2026-10-20 10:44:25  timing: click \-\> listening 0.40s  
2026-10-20 10:44:30  timing: listening \-\> end of speech 5.45s  
2026-10-20 10:44:31  timing: end of speech \-\> text 0.31s  
2026-10-20 10:44:31  you: 4 words  
2026-10-20 10:44:31  action: open ('Settings', 'windows.immersivecontrolpanel\_cw5n1h2txyewy\!microsoft.windows.immersivecontrolpanel')  
2026-10-20 10:44:31  timing: reply start \-\> first sentence 0.00s, its voice 0.14s  
2026-10-20 10:44:31  timing: reply start \-\> first audio 0.15s  
2026-10-20 10:44:33  route: command.act open via rule, total 2.33s \-\> said  
2026-10-20 10:44:33  timing: click \-\> listening 0.39s  
2026-10-20 10:44:37  timing: listening \-\> end of speech 4.39s  
2026-10-20 10:44:38  timing: end of speech \-\> text 0.45s  
2026-10-20 10:44:38  you: 4 words  
2026-10-20 10:44:38  topic memory: 2 topic(s) recalled  
2026-10-20 10:44:38  timing: end of speech \-\> reply start 0.65s  
2026-10-20 10:44:45  timing: reply start \-\> first sentence 6.83s, its voice 0.13s  
2026-10-20 10:44:45  timing: reply start \-\> first audio 6.95s  
2026-10-20 10:44:48  timing: end of speech \-\> reply done 10.76s (llama3.2:3b)  
2026-10-20 10:44:48  clover: 35 characters  
2026-10-20 10:44:48  route: info.chat via model, total 10.76s \-\> answered  
2026-10-20 10:44:49  timing: click \-\> listening 0.39s  
2026-10-20 10:45:15  wake: best 0.84 this minute

