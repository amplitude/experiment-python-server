# Changelog

<!--next-version-placeholder-->

## v1.6.0 (2024-12-20)

### Feature

* Python local evaluation implementation ([#52](https://github.com/amplitude/experiment-python-server/issues/52)) ([`9201cb5`](https://github.com/amplitude/experiment-python-server/commit/9201cb57e6b1b98463b58cdd8275ea2f7286ee49))

## v1.5.0 (2024-12-09)

### Feature

* Support sending evaluated user properties in local evaluation assignment tracking ([#51](https://github.com/amplitude/experiment-python-server/issues/51)) ([`935401a`](https://github.com/amplitude/experiment-python-server/commit/935401a9a077161574a5359f7827aac236c88dbf))

## v1.4.0 (2024-08-27)

### Feature

* Support cohort targeting for local evaluation ([#47](https://github.com/amplitude/experiment-python-server/issues/47)) ([`d8c62c4`](https://github.com/amplitude/experiment-python-server/commit/d8c62c43d0fdae689d0ab85057482146ef90cade))

## v1.3.1 (2024-01-30)

### Fix

* Improve remote evaluation fetch retry logic ([#42](https://github.com/amplitude/experiment-python-server/issues/42)) ([`4864666`](https://github.com/amplitude/experiment-python-server/commit/486466683d787de35fc8a442b0ac060078b4ad81))

## v1.3.0 (2023-12-01)

### Feature

* Evaluation v2 ([#41](https://github.com/amplitude/experiment-python-server/issues/41)) ([`8a57489`](https://github.com/amplitude/experiment-python-server/commit/8a5748933e16ed59207b07b34124952872c42ad5))

## v1.2.4 (2023-10-20)

### Fix

* Memory leak from string cstring disposal ([#40](https://github.com/amplitude/experiment-python-server/issues/40)) ([`93c647f`](https://github.com/amplitude/experiment-python-server/commit/93c647f4da429b75be6eea6c7611b771d4d786cf))

## v1.2.3 (2023-09-19)

### Fix

* Do not track empty assignment events ([#39](https://github.com/amplitude/experiment-python-server/issues/39)) ([`e2fb39a`](https://github.com/amplitude/experiment-python-server/commit/e2fb39a2642d96278b43a4109ee3adb651f91e3a))

## v1.2.2 (2023-09-01)

### Fix

* Allow creation of multiple client instances based on api key ([#38](https://github.com/amplitude/experiment-python-server/issues/38)) ([`b8defe4`](https://github.com/amplitude/experiment-python-server/commit/b8defe43126d48e25e025f1262b0fd01dde19b7f))

## v1.2.1 (2023-08-25)

### Fix

* Update FlagResult class and fix assignment tracking issue ([#37](https://github.com/amplitude/experiment-python-server/issues/37)) ([`6a097cf`](https://github.com/amplitude/experiment-python-server/commit/6a097cfebdd3546d2041679c49ecff81c9482588))
* Provide AssignmentConfig class for use ([#36](https://github.com/amplitude/experiment-python-server/issues/36)) ([`afbd36c`](https://github.com/amplitude/experiment-python-server/commit/afbd36c80048b9e8d9a4c8fd9dbb211d1fc4b9b1))
* Use relative import in LocalEvaluationConfig ([#35](https://github.com/amplitude/experiment-python-server/issues/35)) ([`f5b7897`](https://github.com/amplitude/experiment-python-server/commit/f5b789703b3abb77387ac530526f1550a5a048ed))

## v1.2.0 (2023-08-22)

### Feature

* Automatic assignment tracking ([#25](https://github.com/amplitude/experiment-python-server/issues/25)) ([`f3988fd`](https://github.com/amplitude/experiment-python-server/commit/f3988fded773c06888787339f4cfa1a9e8297867))

## v1.1.3 (2023-07-07)

### Fix

* Update evaluation 1.1.1 ([#24](https://github.com/amplitude/experiment-python-server/issues/24)) ([`ed5924a`](https://github.com/amplitude/experiment-python-server/commit/ed5924af26c93fc9abad6064d0117513dfb3aa2d))

## v1.1.2 (2023-06-09)

### Fix

* Close http connection when request throws exception ([#23](https://github.com/amplitude/experiment-python-server/issues/23)) ([`40c4dbb`](https://github.com/amplitude/experiment-python-server/commit/40c4dbb03961bffaa56138ba5411efda9f2ccd45))

## v1.1.1 (2023-03-29)
### Fix
* Use daemon threads for conn pool and poller ([#20](https://github.com/amplitude/experiment-python-server/issues/20)) ([`fd8360a`](https://github.com/amplitude/experiment-python-server/commit/fd8360a7a8eeff20a97ae41682f794a19c2f568e))

## v1.1.0 (2023-03-14)
### Feature
* Flag dependencies ([#19](https://github.com/amplitude/experiment-python-server/issues/19)) ([`948ecd8`](https://github.com/amplitude/experiment-python-server/commit/948ecd814b373cbe80424bd986fd654e5f83401e))

## v1.0.0 (2022-12-31)
### Fix
* Fix aarch64 ([#18](https://github.com/amplitude/experiment-python-server/issues/18)) ([`546dc8f`](https://github.com/amplitude/experiment-python-server/commit/546dc8f89d30e92a3ddf86189ed4dd1e8e2098a9))

## v0.3.1 (2022-11-21)
### Fix
* Fix linux arm64 load path ([#17](https://github.com/amplitude/experiment-python-server/issues/17)) ([`a6b3de0`](https://github.com/amplitude/experiment-python-server/commit/a6b3de014ea3a6cd219a51a9930af55734b2f146))

## v0.3.0 (2022-09-08)
### Feature
* Add local evaluation library header ([#16](https://github.com/amplitude/experiment-python-server/issues/16)) ([`513f61a`](https://github.com/amplitude/experiment-python-server/commit/513f61af70d971256691afe5b61a119f6fe2b9c7))

### Fix
* Patch for pdoc for local evaluation lib ([#15](https://github.com/amplitude/experiment-python-server/issues/15)) ([`7217110`](https://github.com/amplitude/experiment-python-server/commit/7217110d7bc22169e1ad46ebb01cce029534e5d0))

## v0.2.0 (2022-08-16)
### Feature
* Testing, comments and prepare for release ([#13](https://github.com/amplitude/experiment-python-server/issues/13)) ([`1f38faf`](https://github.com/amplitude/experiment-python-server/commit/1f38faf19bd37e700fa587a738a35e797a6d847f))
* Add local evaluation bootstrap ([#12](https://github.com/amplitude/experiment-python-server/issues/12)) ([`db8c20b`](https://github.com/amplitude/experiment-python-server/commit/db8c20b22317282bafa3955b5a6f98ad6fe05889))
* Add local evaluation library ([#11](https://github.com/amplitude/experiment-python-server/issues/11)) ([`d6aea11`](https://github.com/amplitude/experiment-python-server/commit/d6aea11c806ff2525554631cba1a76522b4b4f31))

### Fix
* Quick fix for ide rename ([#14](https://github.com/amplitude/experiment-python-server/issues/14)) ([`c57610a`](https://github.com/amplitude/experiment-python-server/commit/c57610aac24a2c3202909b597c1f8c76f7bebec6))

## v0.1.0 (2022-06-08)
### Feature
* Timeout tesst and minor fix ([#9](https://github.com/amplitude/experiment-python-server/issues/9)) ([`d6d6e1a`](https://github.com/amplitude/experiment-python-server/commit/d6d6e1aaed64c5486c5cb2a75c40536dadddd78c))
* Add connection pool to support connection reuse ([#8](https://github.com/amplitude/experiment-python-server/issues/8)) ([`e886a7a`](https://github.com/amplitude/experiment-python-server/commit/e886a7af5b80281de6b86ce64902f5c3a6097009))
* Setup release action ([#7](https://github.com/amplitude/experiment-python-server/issues/7)) ([`508364b`](https://github.com/amplitude/experiment-python-server/commit/508364bc30cf98c1b84a905b5fe9ec51f0aaa7d5))
* Add pdoc support ([#6](https://github.com/amplitude/experiment-python-server/issues/6)) ([`71832de`](https://github.com/amplitude/experiment-python-server/commit/71832de6a5603baed2a204a3b36e54b99876a583))
* Add async fetch ([#5](https://github.com/amplitude/experiment-python-server/issues/5)) ([`e17fb0a`](https://github.com/amplitude/experiment-python-server/commit/e17fb0af3b85b01151a2bde3faaaedac27c8d812))
* Add logging support ([#4](https://github.com/amplitude/experiment-python-server/issues/4)) ([`d63c9a3`](https://github.com/amplitude/experiment-python-server/commit/d63c9a393bb761cc52167504d58dfd32cbacdffd))
* Add singleton factory and cookie support ([#3](https://github.com/amplitude/experiment-python-server/issues/3)) ([`4cf2f5a`](https://github.com/amplitude/experiment-python-server/commit/4cf2f5a2d66a116cae4054f69621f749812b0ab5))
* Barebone setup ([`7609d0b`](https://github.com/amplitude/experiment-python-server/commit/7609d0b99b75741200bf84cdfa5cdc0d835ee7d1))
* Basic repo setup ([`5305fb7`](https://github.com/amplitude/experiment-python-server/commit/5305fb7804bdafbe1d0f029e592a44622f19e48c))

### Fix
* Update publish action ([#10](https://github.com/amplitude/experiment-python-server/issues/10)) ([`8da43c1`](https://github.com/amplitude/experiment-python-server/commit/8da43c11bf61566641251f20943efcbf4f70b3ea))
