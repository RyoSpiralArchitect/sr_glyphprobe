# ホールドアウトの状態

[English](HOLDOUT_STATUS.md) · [機械可読の事故記録](../validation/holdout_exposure_incidents/2026-08-07-repository-search.json) · [科学的主張の契約](SCIENTIFIC_CONTRACT.ja.md)

## 現在の状態

P2 v1 bankは、凍結済みMilestone 2プロトコルによって一度だけ開いた、歴史的な
確認用inputである。未使用bankとして扱ったり、再利用したりしてはならない。

C1 v1 bankは、今後の確認・因果実験には使用しない。2026-08-07、read-onlyで行った
リポジトリ検索の範囲が広すぎたため、C1の完全な1レコードが研究agentの文脈へ表示された。
このレコードを使った実験modelのforward、tokenizer処理、outcome解析、panel選択、
endpoint選択は行っていない。それでも、因果プロトコルの凍結前にC1を研究agentの文脈へ
渡さないという、リポジトリの厳格な規則には反している。したがって、このbankを
完全に未露出とは呼べない。

露出したprompt本文は、公開文書へ転載しない。C1 v1 fileは歴史的証拠としてそのまま
保存するが、内容を見ずにfileの存在・size・hashを検査する場合だけアクセスを許可する。将来の因果実験では、
露出した研究文脈の外で、新しいversionのbankを作る必要がある。

## Llama MPS transport studyへの影響

Llama 3.2 3B MPS絵文字transport studyは、P2もC1も使わない。E1と同じ、すでに
探索済みの`prestage_targets`先頭24件だけに固定する。そのため、この事故はこのstudyの
inputやoutcomeを変えない。ただし、公開来歴とPhase IのLimitationsには残す。

## 主張境界

この記録は、C1から科学的outcomeを観測したことを意味しない。研究設計文脈への露出と、
それに伴う保守的なbank廃止を記録するものである。因果主張は認めない。
