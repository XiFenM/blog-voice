下面按 **AI Infra 的四层地图**来收：算力/数据中心、训练与推理系统、数据/RAG/向量库、MLOps/生产化。排序偏“实战含金量”，不是泛 AI 闲聊。🧭

## 1. 值得长期订阅的节目

| 优先级 | 节目                                              | 主要覆盖                                       | 适合听法                                                                                        |
| --- | ----------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------- |
| S   | **Latent Space: The AI Engineer Podcast**       | Foundation models、AI agents、GPU infra、工程实践 | 最像“AI 工程师茶水间里的雷达屏”，适合持续订阅。节目说明明确覆盖 GPU Infra、模型、Agent 等主题。([Apple Podcasts][1])             |
| S   | **MLOps Community Podcast**                     | 生产级 ML/LLM、推理延迟、TensorRT、AI gateways、MLOps | 适合找真实落地案例，官方页有大量生产系统访谈和近期 AI infra 相关单集。([MLOps Community][2])                              |
| S   | **TWIML AI Podcast: AI Infrastructure & MLOps** | AI infra、MLOps、边缘部署、芯片、系统扩展                | TWIML 有专门的 “AI Infrastructure & MLOps” 主题页，适合按专题补课。([TWIML][3])                             |
| S   | **AI Engineering Podcast**                      | 可扩展、可维护 AI 系统，AI 应用架构                      | 偏工程架构，适合 AI app / 平台团队听。节目介绍就是围绕 scalable and maintainable AI systems。([Apple Podcasts][4]) |
| S   | **The Data Exchange with Ben Lorica**           | 数据基础设施、LLMOps、企业 AI 落地                     | 老牌数据/AI 访谈，适合补 data infra、RAG、企业部署。([Apple Podcasts][5])                                    |
| A   | **Gradient Dissent**                            | 模型训练、生产化、W&B 生态、工程团队访谈                     | 适合听“模型如何真的进生产”。节目介绍强调 bringing models into production。([Apple Podcasts][6])                 |
| A   | **Practical AI**                                | MLOps、AIOps、LLMs、实际场景                      | 不只 infra，但偏“怎么落地”，适合作为通勤补丁。([Apple Podcasts][7])                                            |
| A   | **No Priors**                                   | AI 创始人/研究员访谈，含 NVIDIA、Modal 等              | 偏战略和创业，但会有很硬的 infra 嘉宾。([Apple Podcasts][8])                                                |
| A   | **AI + a16z**                                   | AI 创业、基础设施、GPU、AI 产业链                      | 投资视角强，适合看 infra 赛道机会。([Andreessen Horowitz][9])                                             |
| A   | **Training Data by Sequoia**                    | AI builders、研究员、商业/技术趋势                    | 更偏 AI 产业全景，但对模型公司和基础设施趋势有用。([Sequoia Capital][10])                                          |
| A   | **Kubernetes Podcast from Google**              | 云原生、Kubernetes、AI/ML workloads             | 适合关注 K8s 跑 LLM 推理、llm-d、Inference Gateway 的人。([Apple Podcasts][11])                         |
| A   | **Data Center Richness**                        | 数据中心、云、AI infra、能源/冷却/资本开支                 | 物理基础设施必听，偏数据中心产业链。([Apple Podcasts][12])                                                    |
| B   | **NVIDIA AI Podcast**                           | NVIDIA 生态、AI 应用、硬件/产业案例                    | 官方视角，适合跟踪 NVIDIA 生态动向。([Apple Podcasts][13])                                                |
| B   | **Software Engineering Daily**                  | 软件工程、向量搜索、开源模型、推理基础设施                      | 不是纯 AI infra，但经常有相关工程访谈。([Software Engineering Daily][14])                                  |
| B   | **GPU MODE / CUDA Mode 视频音频**                   | GPU 编程、kernel、Triton、CUDA、系统优化             | 不是传统播客，更像硬核课程/讲座，可当音频听。([YouTube][15])                                                      |

## 2. 英文精选单集/访谈

| 主题               | 单集/访谈                                                                                            | 为什么值得听                                                                                                         |
| ---------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| AI 数据中心全栈        | **a16z Show: Building the Real-World Infrastructure for AI, with Google, Cisco & a16z**          | 从芯片、电网、全球数据中心到网络，适合建立 AI infra 的物理世界框架。([Apple Podcasts][16])                                                  |
| GPU 获取与创业公司      | **AI + a16z: How GPU Access Helps Startups Be Agile**                                            | 讲 GPU 短缺、价格波动和创业公司如何拿算力。([Andreessen Horowitz][17])                                                            |
| NVIDIA / 数据中心    | **No Priors: NVIDIA’s Jensen Huang on AI Chip Design, Scaling Data Centers**                     | Jensen 谈 AI 数据中心、NVLink、xAI 超级集群、NVIDIA 长期基础设施下注。([Apple Podcasts][18])                                        |
| NVIDIA / 供应链护城河  | **Dwarkesh Podcast: Jensen Huang – TPU competition, chips to China, Nvidia’s supply-chain moat** | 偏战略、地缘和供应链，适合研究 GPU 生态护城河。([Dwarkesh][19])                                                                     |
| 算力瓶颈             | **Dwarkesh Podcast: Dylan Patel – 3 bottlenecks to scaling AI compute**                          | SemiAnalysis 的 Dylan Patel 深挖 logic、memory、power 三大瓶颈。([Dwarkesh][20])                                         |
| GPU 云商业模式        | **Odd Lots: CoreWeave’s CSO on the Business of Building AI Datacenters**                         | 讲 AI cloud 怎么拿电、选址、融资、区别于传统云。([Apple Podcasts][21])                                                            |
| GPU/TPU 经济学      | **Invest Like the Best: Gavin Baker – Nvidia v. Google, Scaling Laws, and the Economics of AI**  | 偏投资但很适合理解 TPU/GPU、scaling laws、资本开支。([Apple Podcasts][22])                                                     |
| Serverless GPU   | **Latent Space: Truly Serverless Infra for AI Engineers – Erik Bernhardsson of Modal**           | Modal 创始人讲 AI 工程师需要的自服务运行时、GPU 并行、云资源抽象。([潜在空间][23])                                                           |
| ML Infra / Modal | **Gradient Dissent: Elevating ML Infrastructure with Modal Labs CEO Erik Bernhardsson**          | 和上一集互补，偏 ML infra 产品与团队建设。([Spotify][24])                                                                      |
| 推理工程             | **TWIML: How to Engineer AI Inference Systems with Philip Kiely**                                | 2026 年新单集，专讲 inference engineering、GPU programming、distributed systems、model serving 边界。([Apple Podcasts][25]) |
| 推理工程             | **Hanselminutes: Inference Engineering with Baseten’s Philip Kiely**                             | 更入门，围绕 Baseten 的推理工程经验和新书。([Hanselminutes][26])                                                                |
| GPU 云采购          | **AI Engineering Podcast: GPU Clouds, Aggregators, and the New Economics of AI Compute**         | Saturn Cloud CTO 讲 hyperscalers、GPU clouds、bare metal、aggregators 如何选。([Apple Podcasts][27])                   |
| Kubernetes 推理    | **Kubernetes Podcast: LLM-D, with Clayton Coleman and Rob Shaw**                                 | 讲为什么 LLM workload 不同于传统 K8s 工作负载，以及 llm-d / vLLM / Inference Gateway。([kubernetespodcast.com][28])             |
| 数据基础设施           | **O’Reilly: Chang She on Data Infrastructure for AI**                                            | LanceDB 创始人讲为什么传统 data stack 不适合 AI、多模态数据基础设施如何变。([O'Reilly Media][29])                                        |
| 数据/RAG/向量库       | **The Data Stack Show: Generative AI and Data Infrastructure with Chang She**                    | 从 Pandas、LanceDB 到 AI/ML 优化的数据基础设施。([The Data Stack Show][30])                                                 |
| 多模态数据格式          | **The Data Exchange: Unlocking the Power of Unstructured Data**                                  | 讲 Lance 格式、向量索引、非结构化数据、AI workloads。([The Data Exchange][31])                                                  |
| AI-first cloud   | **The Data Exchange: The Infrastructure for Production AI**                                      | Runpod CEO 讲生产 AI cloud、GPU 可靠性、gray outage、agent infra。([The Data Exchange][32])                              |
| 向量搜索             | **Software Engineering Daily: Vespa AI and Surpassing the Limits of Vector Search**              | 适合补 RAG/search infra，不只向量数据库，也涉及更复杂检索需求。([Software Engineering Daily][14])                                     |
| CUDA / GPU 编程    | **Software Unscripted: GPU Programming and Language Design with Chris Lattner**                  | Chris Lattner 讲 GPU/CPU 编程和语言设计，适合底层系统同学。([Apple Podcasts][33])                                                |
| CUDA 生态          | **freeCodeCamp Podcast: CUDA and GPU Programming with Elliot Arledge**                           | 适合想入门 CUDA/GPU 编程的人。([freecodecamp.org][34])                                                                   |
| Data center 视角   | **WIRED Uncanny Valley: How Data Centers Actually Work**                                         | 更偏科普和社会/能源影响，适合理解 AI 数据中心的外部约束。([WIRED][35])                                                                   |
| 会议音视频            | **AI Infra Summit / NVIDIA keynote / 2025 playlist**                                             | 不是播客，但大量会议访谈和主题演讲，适合按硬件、网络、存储、推理专题刷。([AI Infra Summit 2026][36])                                               |

## 3. 中文资源与中文语境单集

中文 AI Infra 的长期节目少，**高质量内容主要散落在单集访谈**里。

| 优先级 | 节目/单集                                              | 重点                                                                             |
| --- | -------------------------------------------------- | ------------------------------------------------------------------------------ |
| S   | **十字路口 Crossing：《AI Infra 就是命运》对谈王雁鹏**             | 从大数据、云计算到 GPU 万卡集群，讲百度 3 万卡集群、中国算力演进、芯片/电力/集群挑战。([Apple Podcasts][37])         |
| S   | **晚点聊 LateTalk：光年之外联创再出发，与袁进辉聊 AI Infra 到底做什么？**   | OneFlow、SiliconFlow、训练框架、推理服务、AI 基础软件商业化。([Apple Podcasts][38])                |
| S   | **潜空间：袁进辉，AI Infra 创业十年得与失**                       | SiliconFlow 创始人复盘分布式编程、推理加速、Infra 创业。([小宇宙][39])                               |
| S   | **OnBoard!: 对话 Lepton AI 创始人贾扬清，AI 需要怎样的基础设施**     | AI 应用运行、云原生 AI 平台、推理基础设施，嘉宾分量很重。([小宇宙][40])                                    |
| A   | **晚点聊：OpenAI o1 来了，与硅流袁进辉聊 o1 新范式和开发者生态**          | 讨论 test-time compute / inference scaling，对推理成本和开发者生态很有用。([Apple Podcasts][41]) |
| A   | **OnBoard!: MosaicML CTO Hanlin Tang 访谈**          | MosaicML、开源 LLM、AI infra 收购、生成式 AI 基础设施竞争。([小宇宙][42])                          |
| A   | **OnBoard!: LanceDB 创始人 Chang She，向量数据库下半场**       | 多模态数据、向量数据库、AI 应用数据基础设施。([小宇宙][43])                                            |
| A   | **OnBoard!: 新一代大模型应用底层技术栈，贾扬清、PingCAP 黄东旭、AWS 嘉宾** | AI-native 软件技术栈、数据存储、开发框架、调试方法。([小宇宙][44])                                     |
| A   | **硅谷101：1 万亿收入预期背后，英伟达的巅峰与软肋**                     | GTC 2026、Blackwell/Vera Rubin、推理效率、芯片、云、软件生态、电力基建。([Apple Podcasts][45])       |
| A   | **硅谷101：科技巨头们开始抢电，AI 用电荒和核聚变创业热**                  | AI 数据中心的电力约束，适合理解 infra 的“水电煤”底盘。([Apple Podcasts][46])                        |
| B   | **潜空间：鱼哲，除 AI Infra 外，还有什么重要的事**                   | Lepton AI 产品负责人谈高性能推理、多云平台、AI infra 创业感受。([小宇宙][47])                           |
| B   | **AI每周谈**                                          | 偏 AI 产业周报，偶尔会覆盖 GPU 集群、资本开支、推理基础设施和上游供应链。([小宇宙][48])                           |

## 4. 推荐播放顺序，10 集入门路线

1. **十字路口：《AI Infra 就是命运》**，先建立中文语境下的算力/集群/芯片框架。([Apple Podcasts][37])
2. **a16z Show: Building the Real-World Infrastructure for AI**，把视野拉到芯片、电网、网络、数据中心全栈。([Apple Podcasts][16])
3. **Dwarkesh: Dylan Patel on scaling AI compute bottlenecks**，补 logic / memory / power 三大硬约束。([Dwarkesh][20])
4. **Odd Lots: CoreWeave’s CSO on AI Datacenters**，理解 GPU cloud 怎么变成资本密集型生意。([Apple Podcasts][21])
5. **Latent Space: Modal / Serverless Infra for AI Engineers**，进入软件抽象层。([潜在空间][23])
6. **TWIML: How to Engineer AI Inference Systems**，聚焦推理工程。([Apple Podcasts][25])
7. **Kubernetes Podcast: LLM-D**，理解 K8s 上的大模型推理为何特殊。([kubernetespodcast.com][28])
8. **O’Reilly: Chang She on Data Infrastructure for AI**，补多模态数据层。([O'Reilly Media][29])
9. **晚点聊：袁进辉聊 AI Infra 到底做什么**，看中国 AI 基础软件创业的现实。([Apple Podcasts][38])
10. **硅谷101：英伟达的巅峰与软肋**，最后回到 NVIDIA 生态、推理拐点和产业链。([Apple Podcasts][45])

我建议先按这个顺序听，像从芯片舱一路走到推理服务舱，最后钻进数据管道，整条 AI infra 飞船的管线图会清楚很多。

[1]: https://podcasts.apple.com/us/podcast/latent-space-the-ai-engineer-podcast/id1674008350?utm_source=chatgpt.com "Latent Space: The AI Engineer Podcast"
[2]: https://home.mlops.community/public/collections/mlops-community-podcast?utm_source=chatgpt.com "MLOps Community Podcast"
[3]: https://twimlai.com/podcast/twimlai/topics/ai-infrastructure-mlops?utm_source=chatgpt.com "AI Infrastructure & MLOps - The Voice of Machine Learning & AI"
[4]: https://podcasts.apple.com/us/podcast/ai-engineering-podcast/id1626358243?utm_source=chatgpt.com "AI Engineering Podcast"
[5]: https://podcasts.apple.com/us/podcast/the-data-exchange-with-ben-lorica/id1487704458?utm_source=chatgpt.com "The Data Exchange with Ben Lorica - Podcast"
[6]: https://podcasts.apple.com/us/podcast/gradient-dissent-conversations-on-ai/id1504567418?utm_source=chatgpt.com "Gradient Dissent: Conversations on AI - Podcast"
[7]: https://podcasts.apple.com/gb/podcast/practical-ai/id1406537385?utm_source=chatgpt.com "Practical AI - Podcast"
[8]: https://podcasts.apple.com/us/podcast/no-priors-artificial-intelligence-technology-startups/id1668002688?utm_source=chatgpt.com "No Priors: Artificial Intelligence | Technology | Startups"
[9]: https://a16z.com/podcasts/ai-a16z/?utm_source=chatgpt.com "AI + a16z"
[10]: https://sequoiacap.com/series/training-data/?utm_source=chatgpt.com "Training Data"
[11]: https://podcasts.apple.com/cm/podcast/kubernetes-podcast-from-google/id1370049232?utm_source=chatgpt.com "Kubernetes Podcast from Google - Émission"
[12]: https://podcasts.apple.com/us/podcast/data-center-richness/id1806129744?utm_source=chatgpt.com "Data Center Richness - Video Podcast"
[13]: https://podcasts.apple.com/us/podcast/nvidia-ai-podcast/id1186480811?utm_source=chatgpt.com "NVIDIA AI Podcast"
[14]: https://softwareengineeringdaily.com/?utm_source=chatgpt.com "Software Engineering Daily"
[15]: https://www.youtube.com/%40GPUMODE/videos?utm_source=chatgpt.com "GPU MODE"
[16]: https://podcasts.apple.com/us/podcast/building-the-real-world-infrastructure-for-ai-with/id842818711?i=1000734025329&utm_source=chatgpt.com "Building the Real-World Infras… - The a16z Show"
[17]: https://a16z.com/podcast/how-gpu-access-helps-startups-be-agile/?utm_source=chatgpt.com "How GPU Access Helps Startups Be Agile"
[18]: https://podcasts.apple.com/nz/podcast/nvidias-jensen-huang-on-ai-chip-design-scaling-data/id1668002688?i=1000676047524&utm_source=chatgpt.com "NVIDIA's Jensen Huang on AI Chip Design, Scaling Data ..."
[19]: https://www.dwarkesh.com/p/jensen-huang?utm_source=chatgpt.com "Jensen Huang – TPU competition, why we should sell ..."
[20]: https://www.dwarkesh.com/p/dylan-patel?utm_source=chatgpt.com "Dylan Patel — Deep dive on the 3 big bottlenecks to ..."
[21]: https://podcasts.apple.com/us/podcast/coreweaves-cso-on-the-business-of-building-ai-datacenters/id1056200096?i=1000659726231&utm_source=chatgpt.com "CoreWeave's CSO on the Busines… - Odd Lots"
[22]: https://podcasts.apple.com/us/podcast/gavin-baker-nvidia-v-google-scaling-laws-and/id1154105909?i=1000740378679&utm_source=chatgpt.com "Gavin Baker - Nvidia v. Google, Scaling Laws, and the ..."
[23]: https://www.latent.space/p/modal?utm_source=chatgpt.com "Truly Serverless Infra for AI Engineers - with Erik ..."
[24]: https://open.spotify.com/episode/0mRirNXiDqHeEhgND7qRZ2?utm_source=chatgpt.com "Elevating ML Infrastructure with Modal Labs CEO Erik ..."
[25]: https://podcasts.apple.com/us/podcast/how-to-engineer-ai-inference-systems-with-philip-kiely/id1116303051?i=1000764990403&utm_source=chatgpt.com "How to Engineer AI Inference Systems with Philip Kiely"
[26]: https://hanselminutes.com/1038/inference-engineering-with-basetens-philip-kiely?utm_source=chatgpt.com "Inference Engineering with Baseten's Philip Kiely"
[27]: https://podcasts.apple.com/sg/podcast/gpu-clouds-aggregators-and-the-new-economics-of-ai-compute/id1626358243?i=1000746844113&utm_source=chatgpt.com "GPU Clouds, Aggregators, and t…–AI Engineering Podcast"
[28]: https://kubernetespodcast.com/episode/258-llmd/?utm_source=chatgpt.com "Episode 258 - LLM-D, with Clayton Coleman and Rob Shaw"
[29]: https://www.oreilly.com/radar/podcast/generative-ai-in-the-real-world-chang-she-on-data-infrastructure-for-ai/?utm_source=chatgpt.com "Generative AI in the Real World: Chang She on Data ..."
[30]: https://datastackshow.com/podcast/the-intersection-of-generative-ai-and-data-infrastructure-with-chang-she-of-lancedb/?utm_source=chatgpt.com "The Intersection of Generative AI and Data Infrastructure ..."
[31]: https://thedataexchange.media/lance-data-format/?utm_source=chatgpt.com "Unlocking the Power of Unstructured Data"
[32]: https://thedataexchange.media/runpod-zhen-lu/?utm_source=chatgpt.com "The Infrastructure for Production AI"
[33]: https://podcasts.apple.com/md/podcast/gpu-programming-and-language-design-with-chris-lattner/id1602572955?i=1000718982830&utm_source=chatgpt.com "GPU Programming and Language Design with Chris Lattner"
[34]: https://www.freecodecamp.org/news/cuda-gpu-programming-elliot-arledge-podcast-155/?utm_source=chatgpt.com "CUDA and GPU Programming with Elliot Arledge [Podcast ..."
[35]: https://www.wired.com/story/uncanny-valley-podcast-how-data-centers-actually-work?utm_source=chatgpt.com "How Data Centers Actually Work"
[36]: https://ai-infra-summit.com/?utm_source=chatgpt.com "AI Infra Summit 2026, Sept, Santa Clara Convention Center"
[37]: https://podcasts.apple.com/us/podcast/ai-infra-%E5%B0%B1%E6%98%AF%E5%91%BD%E8%BF%90-%E5%AF%B9%E8%B0%88%E7%8E%8B%E9%9B%81%E9%B9%8F-%E4%BA%B2%E8%BF%B0%E4%BB%8E%E5%A4%A7%E6%95%B0%E6%8D%AE%E6%97%B6%E4%BB%A3%E5%88%B0-3-%E4%B8%87%E5%8D%A1%E9%9B%86%E7%BE%A4%E7%9A%84%E4%B8%AD%E5%9B%BD%E7%AE%97%E5%8A%9B%E6%BC%94%E8%BF%9B%E5%8F%B2/id1729552193?i=1000734855692 "「AI Infra 就是命运」 | 对谈王雁鹏：亲述从大数据… - 十字路口Crossing - Apple Podcasts"
[38]: https://podcasts.apple.com/ca/podcast/%E5%85%89%E5%B9%B4%E4%B9%8B%E5%A4%96%E8%81%94%E5%88%9B%E5%86%8D%E5%87%BA%E5%8F%91-%E4%B8%8E%E8%A2%81%E8%BF%9B%E8%BE%89%E8%81%8A-ai-infra-%E5%88%B0%E5%BA%95%E5%81%9A%E4%BB%80%E4%B9%88-ai-%E5%A4%A7%E7%88%86%E7%82%B8/id1564877433?i=1000642841343&utm_source=chatgpt.com "光年之外联创再出发，与袁进辉聊AI Infra 到底做什么…"
[39]: https://www.xiaoyuzhoufm.com/episode/6719fe8f0d2f24f28982c3cd?utm_source=chatgpt.com "袁进辉：AI Infra 创业十年得与失| 潜空间"
[40]: https://www.xiaoyuzhoufm.com/episode/65ee7ba02d96b6aa80f4359d?utm_source=chatgpt.com "EP 48. 对话Lepton AI创始人贾扬清：AI需要怎样的基础设施"
[41]: https://podcasts.apple.com/us/podcast/openai-o1-%E6%9D%A5%E4%BA%86-%E4%B8%8E%E7%A1%85%E6%B5%81%E8%A2%81%E8%BF%9B%E8%BE%89%E8%81%8A-o1-%E6%96%B0%E8%8C%83%E5%BC%8F%E5%92%8C%E5%BC%80%E5%8F%91%E8%80%85%E7%94%9F%E6%80%81/id1564877433?i=1000669760627&l=pt-BR&utm_source=chatgpt.com "OpenAI o1 来了！与硅流袁进辉聊o1 新范式和开发者生态"
[42]: https://www.xiaoyuzhoufm.com/episode/656afd428fb8b597a21f6c2e?utm_source=chatgpt.com "创业2年，13亿美金收购，大模型与AI infra的过去与未来"
[43]: https://www.xiaoyuzhoufm.com/episode/66e333da3a5ff0a0ca0e0065?utm_source=chatgpt.com "EP 60. 全英文对话CRV投资人与LanceDB创始人：向量 ..."
[44]: https://www.xiaoyuzhoufm.com/episode/676054e37d8426f6929d67cb?utm_source=chatgpt.com "EP 63. 直播回放：什么是开发大模型应用的新一代底层技术栈 ..."
[45]: https://podcasts.apple.com/us/podcast/e230-1%E4%B8%87%E4%BA%BF%E6%94%B6%E5%85%A5%E9%A2%84%E6%9C%9F%E8%83%8C%E5%90%8E-%E8%8B%B1%E4%BC%9F%E8%BE%BE%E7%9A%84%E5%B7%85%E5%B3%B0%E4%B8%8E%E8%BD%AF%E8%82%8B/id1500662719?i=1000757384562&l=pt-BR&utm_source=chatgpt.com "E230｜1万亿收入预期背后：英伟达的巅峰与软肋— 硅谷101"
[46]: https://podcasts.apple.com/us/podcast/e149-%E7%A7%91%E6%8A%80%E5%B7%A8%E5%A4%B4%E4%BB%AC%E5%BC%80%E5%A7%8B%E6%8A%A2%E7%94%B5-%E8%81%8A%E8%81%8Aai%E7%94%A8%E7%94%B5%E8%8D%92%E5%92%8C%E6%A0%B8%E8%81%9A%E5%8F%98%E5%88%9B%E4%B8%9A%E7%83%AD/id1498541229?i=1000653987633&l=zh-Hans-CN&utm_source=chatgpt.com "E149｜科技巨头们开始抢电？聊聊AI用电荒和核聚变创业热"
[47]: https://www.xiaoyuzhoufm.com/episode/673301b843dc3a4387fc1793?utm_source=chatgpt.com "鱼哲：除AI Infra 外，还有什么重要的事｜潜空间"
[48]: https://www.xiaoyuzhoufm.com/podcast/688a34636f5a275f1cba40fd?utm_source=chatgpt.com "AI每周谈"
