# Atlas 20 Common-Intent Live Usability Test

Live URL: https://2strongtrainers-art.github.io/terrain-environmental-gis/atlas/
Test mode: 390 x 844 mobile Chromium against live production.
Run: 33863032326
Date: 2026-09-04

These are 20 representative high-frequency-style tool-discovery requests across the Atlas's core use cases. They are not claimed to be a statistically ranked top-20 from user analytics.

## Summary
- Structural journey pass: 20/20. Every request produced a route and a non-empty destination.
- Automated top-result keyword relevance: 6/20.
- JavaScript page errors: 0.
- Human review: 2 strong, 3 partial, 15 poor at the top-results level.
- Main issue: the router often selects a broad category and then shows generic category leaders rather than ranking tools for the user's exact task.

| # | Request | First route | Result count | First visible results | Human review |
|---:|---|---|---:|---|---|
| 1 | I need a free AI image generator | Free • No Login | 4 | Explore.org; Dictation.io; LightningMaps; Omni Calculator | Poor |
| 2 | Help me make a short video for social media | AI video & media | 39 | AIFreeVideo; Bing Video; Topaz Video AI; Pika; Synthesia | Strong |
| 3 | I need to design a logo | Design & creative | 313 | Atlassian Design; Google UX Design; Material Design; Parsons Design School; Motion Design School | Partial |
| 4 | Help me build a resume | Design & creative | 313 | Atlassian Design; Google UX Design; Material Design; Parsons Design School; Motion Design School | Poor |
| 5 | I need to edit or work with a PDF | Learning & research | 90 | Research Methods in Psych; Roam Research; 3D Slicer; AddGene; Allen Brain Atlas | Poor |
| 6 | Summarize a research paper | Learning & research | 90 | Research Methods in Psych; Roam Research; 3D Slicer; AddGene; Allen Brain Atlas | Partial |
| 7 | Give me a citation generator | Learning & research | 90 | Research Methods in Psych; Roam Research; 3D Slicer; AddGene; Allen Brain Atlas | Poor |
| 8 | I want to learn Python for free | Free • No Login | 4 | Explore.org; Dictation.io; LightningMaps; Omni Calculator | Poor |
| 9 | I need a calculator for a math problem | Learning & research | 90 | Research Methods in Psych; Roam Research; 3D Slicer; AddGene; Allen Brain Atlas | Poor |
| 10 | Make a QR code | AI & automation | 5 | ManyChat; Claude Code; Genspark; Graphite; Manus | Poor |
| 11 | Show me a useful weather or map tool | Games, maps & 3D | 47 | Azgaar's Map Gen; BlueMap; MapartCraft; MapVerse; MCSeedMap | Partial |
| 12 | Remove the background from an image | Design & creative | 313 | Atlassian Design; Google UX Design; Material Design; Parsons Design School; Motion Design School | Poor |
| 13 | Transcribe audio or a voice recording | AI video & media | 39 | AIFreeVideo; Bing Video; Topaz Video AI; Pika; Synthesia | Poor |
| 14 | I need an AI voice generator | AI video & media | 39 | AIFreeVideo; Bing Video; Topaz Video AI; Pika; Synthesia | Poor |
| 15 | Help me build a website without coding | AI & automation | 5 | ManyChat; Claude Code; Genspark; Graphite; Manus | Poor |
| 16 | Create a presentation or slideshow | Learning & research | 90 | Research Methods in Psych; Roam Research; 3D Slicer; AddGene; Allen Brain Atlas | Poor |
| 17 | Check my writing and grammar | Learning & research | 90 | Research Methods in Psych; Roam Research; 3D Slicer; AddGene; Allen Brain Atlas | Poor |
| 18 | Translate text into another language | Learning & research | 90 | Research Methods in Psych; Roam Research; 3D Slicer; AddGene; Allen Brain Atlas | Poor |
| 19 | Find free stock photos | Free • No Login | 4 | Explore.org; Dictation.io; LightningMaps; Omni Calculator | Poor |
| 20 | Find a free tool I can use without creating an account | Free • No Login | 4 | Explore.org; Dictation.io; LightningMaps; Omni Calculator | Strong |

## Recommended repair
1. Rank against the user's full query across all 1,834 records before falling back to a category route.
2. Extract task intent separately from modifiers such as free, no-login, beginner, AI, and mobile.
3. Do not let the word "free" force the strict four-item Free • No Login collection unless the user also asks for no account/login.
4. Apply weighted scoring: exact task/title match > description/capability match > category match > source category.
5. Preserve relevant-query terms after routing so a category opens pre-filtered and relevance-sorted, not as a generic category listing.
6. Add curated synonyms/intents for PDF, resume, logo, citations, Python learning, calculators, QR codes, background removal, transcription, voice generation, website builders, presentations, grammar, translation, and stock photos.
7. For compound requests such as "weather or map tool", prefer exact matching tools before broad Gaming/Maps category results.
