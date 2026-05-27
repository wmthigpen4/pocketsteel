# Chunk Quality Triage

Scope: read-only triage of `corpus-unified/reports/unified_chunk_issues.tsv`. No corpus files, vector data, embeddings, or scraper outputs were modified.

Status: YELLOW - approved for retrieval/API integration with known risks, not production-quality signoff.

## Summary
- Flagged issue rows: `61,521`
- Bucket method: heuristic classification from issue type, token estimate, metadata presence, post count, and excerpt patterns.
- Bucket counts are primary buckets; each flagged issue row is assigned to one bucket.

## Bucket Counts
| bucket | count |
| --- | ---: |
| false positives | 43,629 |
| low-value tiny chunks | 10,455 |
| oversized chunks | 3,788 |
| duplicated/repeated text | 128 |
| mostly quotes | 48 |
| mostly links | 1,670 |
| missing metadata | 29 |
| possible mixed-topic chunks | 1,774 |

## Buckets By Original Issue Type
| issue type | false positives | low-value tiny chunks | oversized chunks | duplicated/repeated text | mostly quotes | mostly links | missing metadata | possible mixed-topic chunks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| huge_chunk | 0 | 0 | 3,197 | 11 | 5 | 107 | 3 | 1,566 |
| junk_phrase | 43,629 | 1,026 | 591 | 71 | 41 | 1,149 | 20 | 208 |
| tiny_chunk | 0 | 8,599 | 0 | 46 | 2 | 406 | 5 | 0 |
| very_tiny_chunk | 0 | 830 | 0 | 0 | 0 | 8 | 1 | 0 |

## Buckets By Source System
| source system | false positives | low-value tiny chunks | oversized chunks | duplicated/repeated text | mostly quotes | mostly links | missing metadata | possible mixed-topic chunks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| sgf_phpbb_current | 34,934 | 6,975 | 3,469 | 126 | 48 | 1,406 | 29 | 1,649 |
| sgf_ubb_legacy | 8,695 | 3,480 | 319 | 2 | 0 | 264 | 0 | 125 |

## Top Forums By Flagged Rows
| forum | flagged rows |
| --- | ---: |
| Pedal Steel | 19,586 |
| Electronics | 13,830 |
| Steel Players | 11,464 |
| Steel on the Web | 5,026 |
| Tablature | 4,311 |
| Steel Without Pedals | 3,745 |
| No Peddlers | 2,518 |
| Recording | 421 |
| New Product Announcements | 251 |
| Band-in-a-Box | 194 |
| Builders' Corner | 155 |
| Slide Guitar and String Bender Guitars | 20 |

## Sample Rows

### false positives
- `sgf_phpbb_current:forum-11:thread-100049:chunk-0001`
  - Original issue: `junk_phrase` / `thanks`
  - Forum: `Electronics`
  - Thread: `? For Brad Sarno or Ken Fox`
  - Reason: phrase `thanks` appears inside a substantive chunk
  - Excerpt: David Mullis / 2 Jan 2007 7:17 am Howdy! I was looking at Brads Session 400 Geek page, which prompted me to check the filter caps on the Session 400 I picked up last week. Sure enough, the caps needed replacement because they are physically leaking electrol...
- `sgf_phpbb_current:forum-11:thread-100295:chunk-0001`
  - Original issue: `junk_phrase` / `thanks`
  - Forum: `Electronics`
  - Thread: `Trans Tube owners .. help with volume and noise`
  - Reason: phrase `thanks` appears inside a substantive chunk
  - Excerpt: Scott Appleton / 4 Jan 2007 4:58 pm It seems that when you want a clean tone and want to use the tube emulator your noise floor goes way up and you don't have as much gain as your regular amp does.. What it seems is that my 100 watt tube amp is louder witho...

### low-value tiny chunks
- `sgf_phpbb_current:forum-11:thread-100730:chunk-0002`
  - Original issue: `tiny_chunk` / `token_estimate=68`
  - Forum: `Electronics`
  - Thread: `Peavey's Batteryless ProFex11 battery mod ?`
  - Reason: token_estimate=68
  - Excerpt: basilh / 10 Jan 2007 5:14 am Since Peavey didn't know about the mod, they would have restored it to factory specs, which included a battery. ? A FLAT one ? Top Since Peavey didn't know about the mod, they would have restored it to factory specs, which inclu...
- `sgf_phpbb_current:forum-11:thread-100844:chunk-0002`
  - Original issue: `very_tiny_chunk` / `token_estimate=29`
  - Forum: `Electronics`
  - Thread: `speaker cabinets`
  - Reason: token_estimate=29
  - Excerpt: David Doggett / 12 Jan 2007 11:38 am Rick Johnson on the Forum makes great cabinets. Top Rick Johnson on the Forum makes great cabinets.

### oversized chunks
- `sgf_phpbb_current:forum-11:thread-100842:chunk-0005`
  - Original issue: `huge_chunk` / `token_estimate=1297`
  - Forum: `Electronics`
  - Thread: `Looking for advice or ideas`
  - Reason: token_estimate=1297
  - Excerpt: Darryl Logue / 12 Jan 2007 6:14 pm Dave, I also play steel 80% six string 20% It can be a comprimise. I use a 80's mesa boogie mark III . It needs strong tubes and correct bias to keep it in the clean headroom zone. Similiar to a twin (still heavy) with mor...
- `sgf_phpbb_current:forum-11:thread-103386:chunk-0001`
  - Original issue: `huge_chunk` / `token_estimate=1201`
  - Forum: `Electronics`
  - Thread: `Thank goodness... BMI, JCH, etc. =  no EMF`
  - Reason: token_estimate=1201
  - Excerpt: Ray Minich / 14 Feb 2007 12:16 pm Is EMF radiation the cigarette of the 21st century? David Benjamin EE Times (02/13/2007 3:53 PM EST) BARCELONA, Spain  In arguing for widespread adoption of its new My Wi-Guard technology to protect mobile phone users from...

### duplicated/repeated text
- `sgf_phpbb_current:forum-11:thread-103646:chunk-0007`
  - Original issue: `huge_chunk` / `token_estimate=1251`
  - Forum: `Electronics`
  - Thread: `Webb Amplifier Update`
  - Reason: repeated_sentences=2, repeated_ngram_max=2
  - Excerpt: Kevin Hatton / 26 Feb 2007 1:07 pm Amen Jim. Thank goodness for Tom Bradshaw. The Webb is just a smoke'n fabulous amp. Top Amen Jim. Thank goodness for Tom Bradshaw. The Webb is just a smoke'n fabulous amp. Brad Sarno / 26 Feb 2007 3:55 pm Ken, very good to...
- `sgf_phpbb_current:forum-11:thread-125215:chunk-0001`
  - Original issue: `junk_phrase` / `sold`
  - Forum: `Electronics`
  - Thread: `Two Nashville 112's or 1 Nashville 1000 ???  Choice`
  - Reason: repeated_sentences=2, repeated_ngram_max=2
  - Excerpt: Norris Ashment / 11 Jan 2008 5:03 pm What would be your choice. Please don't let the weight of each be the issue. Just the sound and tone ect. Top What would be your choice. Please don't let the weight of each be the issue. Just the sound and tone ect. Sam...

### mostly quotes
- `sgf_phpbb_current:forum-11:thread-293021:chunk-0003`
  - Original issue: `junk_phrase` / `sold`
  - Forum: `Electronics`
  - Thread: `Jbl K-130 ?`
  - Reason: 4 quote markers
  - Excerpt: Mike Neer / 24 Nov 2015 3:28 pm Bill Hatcher wrote: Brad Sarno wrote: Is there a better speaker for steel than a K130? Isn't that the benchmark? B as much as i love the old jbl stuff, i think that the altec 418b Bill Hatcher wrote: Brad Sarno wrote: Is ther...
- `sgf_phpbb_current:forum-11:thread-320715:chunk-0008`
  - Original issue: `junk_phrase` / `bump`
  - Forum: `Electronics`
  - Thread: `iPad apps that you may have missed......`
  - Reason: 4 quote markers
  - Excerpt: Richard Sinkler / 9 Jun 2019 2:39 pm James Mayer wrote: Jon Light wrote: Thanks. No problem. James Mayer wrote: Jon Light wrote: Thanks. No problem. I'm curious what you think of Android music apps. I read somewhere that the reason why there are so few audi...

### mostly links
- `sgf_phpbb_current:forum-11:thread-100614:chunk-0001`
  - Original issue: `tiny_chunk` / `token_estimate=55`
  - Forum: `Electronics`
  - Thread: `Fender Steel King on ebay`
  - Reason: 2 link markers in excerpt
  - Excerpt: David Biggers / 8 Jan 2007 11:44 am I am not sure if anyone cares but I saw this on ebay and thought somone might be looking. click here Top I am not sure if anyone cares but I saw this on ebay and thought somone might be looking. click here
- `sgf_phpbb_current:forum-11:thread-101774:chunk-0001`
  - Original issue: `tiny_chunk` / `token_estimate=73`
  - Forum: `Electronics`
  - Thread: `New tuner`
  - Reason: 4 link markers in excerpt
  - Excerpt: Roger Light / 24 Jan 2007 1:49 pm Anybody see this yet? For those still using a rack. http://www.petersontuners.com/products/ ... /index.cfm Top Anybody see this yet? For those still using a rack. http://www.petersontuners.com/products/ ... /index.cfm

### missing metadata
- `sgf_phpbb_current:forum-5:thread-165192:chunk-0004`
  - Original issue: `junk_phrase` / `sold`
  - Forum: `Pedal Steel`
  - Thread: `Derby  History`
  - Reason: post_uids
  - Excerpt: Jerry Overstreet / 6 Jan 2026 12:19 pm No, that guitar is probably converted from a Double Neck. There has been a lot of that happening unfortunately. I'm pretty sure I remember the Lloyd guitar and I certainly don't recall a cutout on the endplate, but the...
- `sgf_phpbb_current:forum-5:thread-165192:chunk-0005`
  - Original issue: `junk_phrase` / `sold`
  - Forum: `Pedal Steel`
  - Thread: `Derby  History`
  - Reason: post_uids
  - Excerpt: Ricky Davis / 9 Jan 2026 6:14 am You know its a GREAT STEEL when Terry Crisp plays one on this HUGE SOLO at a Reba Show... His long solo starts 1:17 https://youtu.be/IxuVoLt1yHs?si=-7tRp7251QQAaMMk Gotta Love that Terry Crisp Perfection. Ricky https://youtu...

### possible mixed-topic chunks
- `sgf_phpbb_current:forum-11:thread-101699:chunk-0002`
  - Original issue: `huge_chunk` / `token_estimate=1608`
  - Forum: `Electronics`
  - Thread: `zxzz`
  - Reason: token_estimate=1608, post_uids=3
  - Excerpt: Rick Johnson / 24 Jan 2007 5:51 am I know just enough to get by. You should consult a qualified electrician about your problems. ASAP. Rick www.rickjohnsoncabs.com Last edited by Rick Johnson on 24 Jan 2007 8:05 am, edited 1 time in total. Top I know just e...
- `sgf_phpbb_current:forum-11:thread-102030:chunk-0001`
  - Original issue: `huge_chunk` / `token_estimate=1587`
  - Forum: `Electronics`
  - Thread: `steel guitar electronic accessory`
  - Reason: token_estimate=1587, post_uids=6
  - Excerpt: Dean Schrock / 27 Jan 2007 8:44 pm here is my question, If you was limited to use just one electronic gaget or accessory or what ever you want to call it, here is my question, If you was limited to use just one electronic gaget or accessory or what ever you...

## Interpretation
- Most `junk_phrase` flags are false positives because words such as `thanks`, `sold`, or `bump` appear inside otherwise substantive chunks.
- The main cleanup candidates are low-value tiny chunks, oversized chunks, link-heavy rows, and possible mixed-topic chunks.
- Phase 3 remains blocked: fixing these in the live index would require approved corpus/chunking changes and a later embedding refresh.
