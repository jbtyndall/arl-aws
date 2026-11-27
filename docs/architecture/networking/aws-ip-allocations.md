# AWS IP Allocations

| VPC | VPC CIDR | Subnet | Subnet CIDR | Notes
|--- | --- | --- | --- | ---
| **its-shared-vpc** | **10.251.0.0/18** | | | **Shared VPC in the ITS Shared Services account**<br>Hosts shared subnets for project accounts not requiring VPC-level isolation (i.e. non-enclave)
| | | its-shared-tgw-subnet-a | 10.251.0.0/28 | Transit Gateway attachment subnet in AZ A
| | | its-shared-tgw-subnet-b | 10.251.0.16/28 | Transit Gateway attachment subnet in AZ B
| | | its-shared-tgw-subnet-c | 10.251.0.32/28 | Transit Gateway attachment subnet in AZ C
| | | its-shared-testproject-subnet-a | 10.251.1.0/24 | Project subnet - ITS Sandbox
| **its-sandbox-vpc** | **10.251.64.0/24** | | | **Project VPC - ITS-Sandbox**
| | | its-sandbox-subnet-a | 10.251.64.0/25 | Project subnet in AZ A
| | | its-sandbox-subnet-b | 10.251.64.128/25 | Project subnet in AZ B
| **cino-verde-vpc** | **10.251.65.0/24** | | | **Project VPC - CINO-VERDE**
| | | cino-verde-subnet-a | 10.251.65.0/25 | Project subnet in AZ A
| | | cino-verde-subnet-b | 10.251.65.128/25 | Project subnet in AZ B
| **cino-whiteout-vpc** | **10.251.66.0/24** | | | **Project VPC - CINO-WhiteOut**
| | | cino-whiteout-subnet-a | 10.251.66.0/25 | Project subnet in AZ A
| | | cino-whiteout-subnet-b | 10.251.66.128/25 | Project subnet in AZ B
| **cino-cloudfish-vpc** | **10.251.67.0/24** | | | **Project VPC - CINO-Cloudfish**
| | | cino-cloudfish-subnet-a | 10.251.67.0/25 | Project subnet in AZ A
| | | cino-cloudfish-subnet-b | 10.251.67.128/25 | Project subnet in AZ B
| **uso-rail-vpc** | **10.251.68.0/24** | | | **Project VPC - USO-RAIL**
| | | uso-rail-subnet-a | 10.251.68.0/25 | Project subnet in AZ A
| | | uso-rail-subnet-b | 10.251.68.128/25 | Project subnet in AZ B
| **mmo-iirm-vpc** | **10.251.69.0/24** | | | **Project VPC - MMO-IIRM-SEAL**
| | | mmo-iirm-subnet-a | 10.251.69.0/25 | Project subnet in AZ A
| | | mmo-iirm-subnet-b | 10.251.69.128/25 | Project subnet in AZ B
| **cino-stardust-vpc** | **10.251.70.0/24** | | | **Project VPC - CINO-STARDUST**
| | | cino-stardust-subnet-a | 10.251.70.0/25 | Project subnet in AZ A
| | | cino-stardust-subnet-b | 10.251.70.128/25 | Project subnet in AZ B
| **cino-de-vpc** | **10.251.71.0/24** | | | **Project VPC - CINO-DE**
| | | cino-de-subnet-a | 10.251.71.0/25 | Project subnet in AZ A
| | | cino-de-subnet-b | 10.251.71.128/25 | Project subnet in AZ B
| **sil-mvp-vpc** | **10.251.72.0/24** | | | **Project VPC - SIL-MVP**
| | | sil-mvp-subnet-a | 10.251.72.0/25 | Project subnet in AZ A
| | | sil-mvp-subnet-b | 10.251.72.128/25 | Project subnet in AZ B
| | **10.251.73.0/24** | | |
| | | | 10.251.73.0/25 | Project subnet in AZ A
| | | | 10.251.73.128/25 | Project subnet in AZ B
| **cino-gds-vpc** | **10.251.74.0/24** | | | **Project VPC - CINO-GDS**
| | | cino-gds-subnet-a | 10.251.74.0/25 | Project subnet in AZ A
| | | cino-gds-subnet-b | 10.251.74.128/25 | Project subnet in AZ B
| **msa-advmdatainfra-vpc** | **10.251.75.0/24** | | | **Project VPC - MSA-AdvDataInfra**
| | | msa-advmdatainfra-subnet-a | 10.251.75.0/25 | Project subnet in AZ A
| | | msa-advmdatainfra-subnet-b | 10.251.75.128/25 | Project subnet in AZ B
| **mmso-oex-communications-vpc** | **10.251.76.0/24** | | | **Project VPC - MMSO-OEX-Communications**
| | | mmso-oex-communications-subnet-a | 10.251.76.0/25 | Project subnet in AZ A
| | | mmso-oex-communications-subnet-b | 10.251.76.128/25 | Project subnet in AZ B
| **a2so-x-mmso-llmdesignoptimization-vpc** | **10.251.77.0/24** | | | **Project VPC - A2SO-x-MMSO-LLMDesignOptimization**
| | | a2so-x-mmso-llmdesignoptimization-subnet-a | 10.251.77.0/25 | Project subnet in AZ A
| | | a2so-x-mmso-llmdesignoptimization-subnet-b | 10.251.77.128/25 | Project subnet in AZ B
| **gids-basecamp-vpc** | **10.251.78.0/24** | | | **Project VPC - GIDS-Basecamp**
| | | gids-basecamp-subnet-a | 10.251.78.0/25 | Project subnet in AZ A
| | | gids-basecamp-subnet-b | 10.251.78.128/25 | Project subnet in AZ B
| **ats-modernshipcheck-vpc** | **10.251.79.0/24** | | | **Project VPC - ATS-ModernShipcheck**
| | | ats-modernshipcheck-subnet-a | 10.251.79.0/25 | Project subnet in AZ A
| | | ats-modernshipcheck-subnet-b | 10.251.79.128/25 | Project subnet in AZ B
| **cms-cta-department-vpc** | **10.251.80.0/24** | | | **Project VPC - CMS-CTA-Department**
| | | cms-cta-department-subnet-a | 10.251.80.0/25 | Project subnet in AZ A
| | | cms-cta-department-subnet-b | 10.251.80.128/25 | Project subnet in AZ B
| **gids-nimbus-vpc** | **10.251.81.0/24** | | | **Project VPC - GIDS-Nimbus**
| | | gids-nimbus-subnet-a | 10.251.81.0/25 | Project subnet in AZ A
| | | gids-nimbus-subnet-b | 10.251.81.128/25 | Project subnet in AZ B
| **cms-j9-rag-vpc** | **10.251.82.0/24** | | | **Project VPC - CMS-J9-RAG**
| | | cms-j9-rag-subnet-a | 10.251.82.0/25 | Project subnet in AZ A
| | | cms-j9-rag-subnet-b | 10.251.82.128/25 | Project subnet in AZ B
| **gids-dcs-vpc** | **10.251.83.0/24** | | | **Project VPC - GIDS-DCS**
| | | gids-dcs-subnet-a | 10.251.83.0/25 | Project subnet in AZ A
| | | gids-dcs-subnet-b | 10.251.83.128/25 | Project subnet in AZ B
| **gids-nimbus-vpc** | **10.251.84.0/24** | | | **Project VPC - GIDS-Nimbus**
| | | gids-nimbus-subnet-c | 10.251.84.0/25 | Project subnet in AZ A
| | | \<unallocated\> | 10.251.83.128/25 | |
| **its-kionTEST-vpc** | **10.251.250.0/24** | | | **KionTEST VPC in the ITS Governance account**
| | | its-kionTEST-subnet-a | 10.251.250.0/27 | Application node subnet in AZ A
| | | its-kionTEST-subnet-b | 10.251.250.32/27 | Application node subnet in AZ B
| **its-cloudtamer-vpc** | **10.251.250.0/24** | | | **Cloudtamer VPC in the ITS Governance account**
| | | its-cloudtamer-private-subnet-a | 10.251.250.0/27 | Application node subnet in AZ A
| | | its-cloudtamer-private-subnet-b | 10.251.250.32/27 | Application node subnet in AZ B
| | | its-cloudtamer-public-subnet-a | 10.251.250.128/27 | User-facing subnet in AZ A
| | | its-cloudtamer-public-subnet-b | 10.251.250.160/27 | User-facing subnet in AZ B