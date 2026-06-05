import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, f1_score

# 该函数用于评估模型的性能，计算准确率、精确度和 F1 分数。
# 参数：
#   real_file (str): 包含实际标签（'id' 和 'result' 列）的 Excel 文件路径。
#   pred_file (str): 包含预测标签（'id' 和 'result' 列）的 Excel 文件路径。
def evaluate_model_performance(real_file, pred_file):
    # 1. 读取 Excel 文件
    real_df = pd.read_excel(real_file)  # 包含 'id' 和 'result' 列
    pred_df = pd.read_excel(pred_file)  # 包含 'id' 和 'result' 列

    # 2. 合并数据：按 'id' 对齐
    merged = pd.merge(
        real_df[['id', 'result']],
        pred_df[['id', 'result']],
        on='id',
        how='inner',
        suffixes=('_actual', '_pred')
    )

    # 3. 将类别标签编码为整数
    le = LabelEncoder()
    merged['y_true'] = le.fit_transform(merged['result_actual'])
    merged['y_pred'] = le.transform(merged['result_pred'])

    # 4. 计算指标
    acc = accuracy_score(merged['y_true'], merged['y_pred'])
    pre = precision_score(merged['y_true'], merged['y_pred'], average='weighted')
    f1 = f1_score(merged['y_true'], merged['y_pred'], average='weighted')

    # 5. 输出结果
    results = {
        'Accuracy': acc,
        'Precision': pre,
        'F1 Score': f1
    }

    return results

if __name__ == "__main__":
    # 示例调用
    real_file = '附件3：结特征.xlsx'  # 实际标签文件路径
    pred_file = '附件8：最终预测结果-ds.xlsx'  # 预测标签文件路径

    metrics = evaluate_model_performance(real_file, pred_file)

    # 打印输出
    print(f"Accuracy:  {metrics['Accuracy']:.4f}")
    print(f"Precision: {metrics['Precision']:.4f}")
    print(f"F1 Score:  {metrics['F1 Score']:.4f}")
