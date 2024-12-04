from functools import partial


def month_ratio(year_rate, month):
    return (1 + year_rate / 12) ** month


def binary_search(l, r, check):
    while l + 1e-8 < r:
        mid = (l + r) / 2
        if check(mid):
            l = mid
        else:
            r = mid
    return l


def judge(
    r,
    principal,
    rebate,
    inflow_list,
    info=False,
):
    inflow_total_present = 0

    for idx, inflow in enumerate(inflow_list):
        t = idx + 1
        inflow_term_present = inflow / month_ratio(r, t)
        if info:
            print("第{}期\t{}".format(t, inflow_term_present))
        inflow_total_present += inflow_term_present

    cost_total_present = principal - rebate

    diff = inflow_total_present - cost_total_present

    if info:
        print("流入现值总和\t{}".format(inflow_total_present))
        print("流出现值总和\t{}".format(cost_total_present))

    return diff > 0


def irr(principal, rebate, inflow_list, info):
    """
    principal                       本金
    rebate                          回扣
    inflow_list                     每期现金流
    """
    check = partial(
        judge,
        principal=principal,
        rebate=rebate,
        inflow_list=inflow_list,
        info=info,
    )
    check_with_info = partial(
        judge,
        principal=principal,
        rebate=rebate,
        inflow_list=inflow_list,
        info=True,
    )
    r = binary_search(0.0, 10.0, check)
    check_with_info(r)
    print("\n-------------\n年化利率: {:.2f}%\n-------------\n".format(r * 100))


inflow_list = [9696 for _ in range(143)]
inflow_list.append(76305.06)
irr(
    principal=1.2e6,
    rebate=0,
    inflow_list=inflow_list,
    info=False,
)
