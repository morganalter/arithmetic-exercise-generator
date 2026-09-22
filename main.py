import argparse
import random
import sys
import os
import re
from fractions import Fraction


def format_fraction(f):
    num = f.numerator
    den = f.denominator
    if den == 1:
        return str(num)
    integer = num // den
    remain = num % den
    if integer == 0:
        return f"{remain}/{den}"
    else:
        return f"{integer}’{remain}/{den}"


def parse_fraction(s):
    s = s.strip()
    if "’" in s:
        int_part, frac_part = s.split("’")
        n, d = map(int, frac_part.split("/"))
        return Fraction(int(int_part) * d + n, d)
    elif "/" in s:
        n, d = map(int, s.split("/"))
        return Fraction(n, d)
    else:
        return Fraction(int(s), 1)


class ExprNode:
    def __init__(self, value=None, op=None, left=None, right=None):
        self.value = value
        self.op = op
        self.left = left
        self.right = right

    def is_leaf(self):
        return self.value is not None


def gen_number(r):
    if r < 2 or random.choice([True, False]):
        n = random.randint(0, r - 1)
        return ExprNode(value=Fraction(n, 1))
    else:
        den = random.randint(2, r - 1)
        int_part = random.randint(0, r - 1)
        num = random.randint(1, den - 1)
        total = int_part * den + num
        return ExprNode(value=Fraction(total, den))


def evaluate(node):
    if node.is_leaf():
        return node.value
    l = evaluate(node.left)
    r = evaluate(node.right)
    if node.op == '+':
        return l + r
    elif node.op == '-':
        return l - r
    elif node.op == '×':
        return l * r
    elif node.op == '÷':
        return l / r


def _gen_expr(op_cnt, r):
    if op_cnt == 0:
        return gen_number(r)

    ops = ['+', '-', '×', '÷']
    if r < 2:
        ops = ['+', '-', '×']
    op = random.choice(ops)

    left_ops = random.randint(0, op_cnt - 1)
    right_ops = op_cnt - 1 - left_ops

    left = _gen_expr(left_ops, r)
    if left is None:
        return None
    right = _gen_expr(right_ops, r)
    if right is None:
        return None

    l_val = evaluate(left)
    r_val = evaluate(right)

    if op == '-':
        if l_val < r_val:
            return None
    elif op == '÷':
        if r_val == 0:
            return None
        res = l_val / r_val
        if res.denominator == 1:
            return None

    return ExprNode(op=op, left=left, right=right)


def gen_expression(op_cnt, r):
    for _ in range(1000):
        node = _gen_expr(op_cnt, r)
        if node is not None:
            return node
    raise ValueError(f"数值范围{r}过小，无法生成符合要求的表达式，请增大-r参数")


def get_canonical(node):
    if node.is_leaf():
        return format_fraction(node.value)
    l = get_canonical(node.left)
    r = get_canonical(node.right)
    if node.op in ('+', '×'):
        if l > r:
            l, r = r, l
    return f"({node.op} {l} {r})"


priority = {'+': 1, '-': 1, '×': 2, '÷': 2}


def to_infix(node, parent_op=None, is_right=False):
    if node.is_leaf():
        return format_fraction(node.value)
    cur_op = node.op
    cur_prio = priority[cur_op]
    left_str = to_infix(node.left, cur_op, False)
    right_str = to_infix(node.right, cur_op, True)
    expr = f"{left_str} {cur_op} {right_str}"
    if parent_op is not None:
        par_prio = priority[parent_op]
        if cur_prio < par_prio:
            expr = f"({expr})"
        elif cur_prio == par_prio and is_right:
            expr = f"({expr})"
    return expr


def eval_expr_str(expr_str):
    expr = expr_str.replace('×', '*').replace('÷', '/')
    pattern = r"(\d+’\d+/\d+)|(\d+/\d+)|(\d+)"
    def repl(m):
        f = parse_fraction(m.group(0))
        return f"Fraction({f.numerator}, {f.denominator})"
    expr = re.sub(pattern, repl, expr)
    return eval(expr)


def generate_exercises(n, r):
    exercises = []
    answers = []
    canon_set = set()
    max_total_retries = n * 100
    retry = 0
    while len(exercises) < n:
        retry += 1
        if retry > max_total_retries:
            raise RuntimeError(f"尝试{max_total_retries}次仍无法生成足够的不重复题目，请增大-r参数")
        op_cnt = random.randint(1, 3)
        expr = gen_expression(op_cnt, r)
        canon = get_canonical(expr)
        if canon in canon_set:
            continue
        canon_set.add(canon)
        infix = to_infix(expr)
        exercises.append(f"{infix} =")
        ans = evaluate(expr)
        answers.append(format_fraction(ans))
    with open('Exercises.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(exercises) + '\n')
    with open('Answers.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(answers) + '\n')


def grade(exercise_file, answer_file):
    with open(exercise_file, 'r', encoding='utf-8') as f:
        exercises = [line.strip() for line in f if line.strip()]
    with open(answer_file, 'r', encoding='utf-8') as f:
        user_ans = [line.strip() for line in f if line.strip()]
    correct = []
    wrong = []
    for i in range(len(exercises)):
        ex = exercises[i].rstrip('=').strip()
        ua = user_ans[i]
        correct_val = eval_expr_str(ex)
        user_val = parse_fraction(ua)
        if correct_val == user_val:
            correct.append(i + 1)
        else:
            wrong.append(i + 1)
    with open('Grade.txt', 'w', encoding='utf-8') as f:
        f.write(f"Correct: {len(correct)} ({', '.join(map(str, correct))})\n")
        f.write(f"Wrong: {len(wrong)} ({', '.join(map(str, wrong))})\n")


def main():
    parser = argparse.ArgumentParser(description='小学四则运算题目生成与批改程序')
    parser.add_argument('-n', type=int, help='生成题目的个数')
    parser.add_argument('-r', type=int, help='题目中数值与分母的范围（不包含该值）')
    parser.add_argument('-e', type=str, help='题目文件路径')
    parser.add_argument('-a', type=str, help='答案文件路径')
    args = parser.parse_args()

    if args.e and args.a:
        if not os.path.isfile(args.e):
            print(f"错误：题目文件 {args.e} 不存在")
            sys.exit(1)
        if not os.path.isfile(args.a):
            print(f"错误：答案文件 {args.a} 不存在")
            sys.exit(1)
        grade(args.e, args.a)
        print("批改完成，结果已写入 Grade.txt")
        return

    if args.r is None:
        print("错误：必须指定 -r 参数")
        parser.print_help()
        sys.exit(1)
    if args.r < 1:
        print("错误：-r 必须为正整数")
        sys.exit(1)
    if args.n is None:
        print("错误：必须指定 -n 参数")
        parser.print_help()
        sys.exit(1)
    if args.n < 1:
        print("错误：-n 必须为正整数")
        sys.exit(1)

    try:
        generate_exercises(args.n, args.r)
        print(f"成功生成 {args.n} 道题目")
        print("题目文件：Exercises.txt")
        print("答案文件：Answers.txt")
    except Exception as e:
        print(f"生成失败：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
