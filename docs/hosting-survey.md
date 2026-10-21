# Hosting survey — 16 GB plans against Mikrus 4.2 Pro

**Status: survey, 2026-10-19. Not a decision.** [deployment.md](deployment.md)
still records the host. Nothing here was provisioned or load-tested.

## The Mikrus price on the screenshot

**790 zł is per year, gross, not per month.** Mikrus's own page says every
listed price is the yearly total, renewal equals the purchase price, and
there is no monthly plan. 790 / 12 is about **66 zł per month gross**.

A Polish comparison site converts that, at the 1 Sep 2026 ECB rate, to
**€12.36 per month net** (€148 per year net). Plan: 16 GB RAM, 160 GB NVMe,
Finland, full root, "2× CPU and 2× IOPS". It is an unprivileged LXC
container: shared kernel, no dedicated public IPv4 (a handful of forwarded
ports plus IPv6). Source: [mikr.us](https://mikr.us/) and the 4.2 order page.

`ted106` today is the 8 GB plan (Mikrus 4.1 Pro, 395 zł/year on the same
page). Moving to 4.2 doubles RAM on the same kind of machine.

Langfuse's Compose guide asks for 4 cores and 16 GB, and StackRates lists
Langfuse itself under apps whose docs ask for 4 vCPU, 16 GB, and 100 GB of
disk. RAM is the part 4.2 satisfies. A full virtual machine (KVM) is the
part it does not: ClickHouse on LXC is the risk, and there is still no
normal public IPv4.

## How to read the prices

Comparison prices were checked **19 Oct 2026** on
[StackRates](https://stackrates.ai/vps/16gb-ram/) (USD, often ex VAT) and
[ServerWorth](https://serverworth.com/vps/16gb/) (GBP, UK VAT included, EU
locations). Hetzner's own price table did not render. A Polish buyer pays
23% VAT on top of ex-VAT EU prices; Mikrus's 790 zł already includes VAT.
Intro prices that jump at renewal are marked.

Reddit threads used: r/VPS "Budget VPS for work" (Jul 2026), "Has Contabo
improved?" (2025, still the thread Google surfaces), "Contabo vs OVH"
(Feb 2026), r/hetzner Netcup vs Hetzner (Apr and Jun 2026), r/homelab
Hetzner alternatives (Jun 2026).

## Twenty-four hosts at about 16 GB

Sorted by the monthly price StackRates or ServerWorth showed. The first
rows are the ones in Mikrus's band.

| # | Provider and plan | RAM / CPU / disk | Price | What people say |
|---|-------------------|------------------|-------|-----------------|
| 1 | **Mikrus 4.2 Pro** | 16 GB, shared, 160 GB NVMe, Finland, LXC | 790 zł/year gross (~€12 net/mo) | Already the app's host family. No dedicated IPv4 |
| 2 | **Hostinger KVM 4** | 16 GB, 4 vCPU, 200 GB NVMe | $12.99/mo for 24 months, then higher. ServerWorth lists £29.99 | Cheap only if you prepay two years |
| 3 | **HostHatch NVMe 16 GB** | 16 GB, 4 vCPU, 75 GB NVMe | $15/mo, or £13.50 | r/VPS likes the network. Disk upgrades are expensive. 75 GB is tight for Langfuse |
| 4 | **Hetzner CX43** | 16 GB, 8 shared vCPU, 160 GB NVMe, DE/FI | About $18.49/mo before a ~$0.60 IPv4, hourly. Rose 15 Jun 2026 from $13.99 | The one people move to for snapshots, backups, and a normal API. KVM |
| 5 | **netcup VPS Lite 3** | 16 GB, 8 vCPU, 320 GB | €14/mo, billed two months (HostingPickers, 11 Oct) | Budget line. Confirm it is still listed before buying |
| 6 | **Contabo Cloud VPS 8** | 24 GB, 8 vCPU, 300 GB | $16.80/mo ex VAT | r/VPS, Jul 2026: stay away. Repeated reports of slow CPU, rate limits, weak support |
| 7 | **HOSTKEY vm.v2-medium** | 16 GB, 8 vCPU, 160 GB, Amsterdam | £14.18/mo | On the EU price list. No Reddit thread read for this one |
| 8 | **Gigahost Value** | 16 GB, 8 vCPU, 120 GB, Norway | £17.06/mo | On the EU price list. No Reddit thread read |
| 9 | **Aruba Cloud O8A16** | 16 GB, 8 vCPU, 160 GB NVMe | €19.89/mo ex VAT | Same shape as Mikrus 4.2, real VPS. No Reddit thread read |
| 10 | **Hostodo EPYC 16 GB** | 16 GB, 6 vCPU, 192 GB NVMe | $20/mo | Budget US-leaning host. No Reddit thread read |
| 11 | **OVHcloud VPS-4** | 24 GB, 8 vCPU, 200 GB NVMe | $27.50/mo on StackRates; a 12-month price elsewhere is €19.96 ex VAT | r/VPS, Feb 2026: stable CPU, better than Contabo. One report of flaky DNS |
| 12 | **InterServer 8 slices** | 16 GB, 4 vCPU, 320 GB | $24/mo, price-lock style | Long-running US host. No fresh Reddit thread read |
| 13 | **UpCloud Starter 16 GB** | 16 GB, **2** vCPU, 50 GB | €24/mo, hourly | Fast network, too little CPU and disk for Langfuse |
| 14 | **netcup VPS 2000 G12.5** | 16 GB, 8 shared vCPU, 256 GB | €26.01/mo ex VAT including IPv4 | r/hetzner, 2026: good performance, old panel, weak API, snapshot pain. Fine for one box |
| 15 | **Cherry Servers VDS** | 16 GB, **4 dedicated** vCPU, 100 GB, Stockholm | £29.37/mo | Dedicated cores. No Reddit thread read |
| 16 | **ServaRica FAT Slice 8** | 16 GB, 8 vCPU, 240 GB NVMe | $30/mo | Named on r/VPS as a decent cheap host, often Canada |
| 17 | **Infomaniak 4 vCPU / 16 GB** | 16 GB, 4 vCPU, **20 GB** disk, Geneva | £23.40/mo | Swiss company. The disk is too small |
| 18 | **STRATO VPS XL** | 16 GB, 8 vCPU, 480 GB, Germany | £33.19/mo | Lots of disk. No Reddit thread read |
| 19 | **IONOS VPS XL+** | 16 GB, 8 vCPU, 480 GB | $47/mo on a 12-month bill | r/homelab: usable, dated UI. Intro prices elsewhere are much lower, then jump |
| 20 | **netcup RS 2000 G12** | 16 GB, **8 dedicated** vCPU, 256 GB | £45.80/mo on ServerWorth. One r/VPS post (Apr 2026) reported €18 at 0% VAT | Dedicated cores. Treat the €18 figure as one person's invoice, not the list price |
| 21 | **Scaleway BASIC2 ARM 16 GB** | 16 GB, 4 ARM vCPU, disk billed extra (10 GB in the quote) | £55.59/mo | r/homelab: fine, not Hetzner-cheap. Paris, Amsterdam, Warsaw |
| 22 | **DigitalOcean 16 GB** | 16 GB, 8 vCPU, 320 GB | $96/mo | Boring and expensive. Hourly, good API |
| 23 | **Vultr 16 GB** | 16 GB | about $70–96/mo | Same class as DigitalOcean |
| 24 | **AWS Lightsail 16 GB** | 16 GB, 2 vCPU, 160 GB | about $74/mo, £66.59 with UK VAT | Two cores. Wrong shape for this |
| 25 | **Akamai / Linode 16 GB dedicated** | 16 GB | about $144/mo (pikkly, 18 Oct) | The expensive end |
| 26 | **Hetzner CPX42** | 16 GB, 8 vCPU, 320 GB | About $82/mo after the 15 Jun 2026 rise (was ~$30) | Same company as CX43, much more money. Hourly |

Also seen and not given a row: Kimsufi (OVH eco) had a 32 GB box near $11
and StackRates marked it sold out. Oracle's free ARM tier was not
re-checked. BuyVM did not appear on the 16 GB lists.

## What Reddit repeats

- **Hetzner** when you care about snapshots, backups, resizing, and a
  private network. One person moved a small SaaS off Netcup onto CX43 for
  those reasons and found the disk faster.
- **Netcup** when you want more RAM and cores per euro and can live with a
  clumsy panel and no real API. Root-server (RS) plans are the ones called
  dedicated.
- **OVH** when you want a normal KVM, unmetered traffic, and daily backups,
  and you have already rejected Contabo.
- **Contabo** is the price that looks like Mikrus and the comments say not
  to use for anything that has to stay up.
- **HostHatch** is respected and short on disk.

## Recommendation

Mikrus 4.2 Pro is already the cheap 16 GB option: about €12 net a month,
paid once a year, same provider as `ted106`. It does not become a normal
VPS. Langfuse wants a KVM with 16 GB and about 100 GB of disk.

If the trace UI is the reason to buy 16 GB, take **Hetzner CX43** (hourly,
Germany or Finland, real IPv4, snapshots). It costs more per year than
790 zł and it is the box people in these threads actually keep. **OVH
VPS-4** is the alternative if you want 24 GB and unmetered traffic.
**Netcup VPS 2000** is the alternative if the panel does not matter and the
price does.

Do not take Contabo to save the difference. Do not take Hostinger's $12.99
without reading the renewal. Keep Supabase for Postgres and auth either
way; a bigger VM does not lift the 500 MB free-tier cap.
