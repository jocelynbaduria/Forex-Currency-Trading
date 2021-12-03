# Forex Currency Trading
 Tinkers Project

### Training

To train the model, use the following command:
```shell
$ python3 train.py --train data/EUR_11_09_21.csv --valid EUR_11_09_21.csv --model-type=pg  --episode-count 50 --window-size 10
```

### Evaluation

To evaluate the given model, use the following command:
```shell
$ python3 evaluate.py --eval data/EUR.csv --model-name EUR_11_09_21 --window-size 10 --verbose True
```
