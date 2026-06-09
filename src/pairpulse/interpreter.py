def interpret_rule(rule, group_name=""):
    ante = rule.get("antecedent", "")
    cons = rule.get("consequent", "")
    lift = rule.get("lift", 0)
    conf = rule.get("confidence", 0)
    support = rule.get("support", 0)

    suggestions = []

    if lift >= 3.0:
        suggestions.append({
            "type": "捆绑套餐",
            "priority": "高",
            "reason": f"提升度 {lift:.1f}，关联极强。客户认知中这两件商品是天然配套的，单独买反而奇怪。",
            "action": f"将「{ante}」和「{cons}」组合为固定套餐，命名如'防护套装''下午茶套餐'，比单买优惠 5-10%。",
        })

    elif lift >= 2.0:
        suggestions.append({
            "type": "页面推荐",
            "priority": "高" if conf >= 0.40 else "中",
            "reason": f"置信度 {conf:.0%}，每约 {1/conf:.0f} 个买「{ante}」的人就有 1 个会买「{cons}」。",
            "action": f"在「{ante}」的详情页设置推荐位，标注'买过的人也买了'，推荐「{cons}」。",
        })

    if lift >= 1.5 and conf >= 0.20:
        suggestions.append({
            "type": "陈列调整",
            "priority": "中",
            "reason": f"提升度 {lift:.1f}，置信度 {conf:.0%}，客户倾向于一起购买但关联不如强配套那么紧密。",
            "action": f"将「{ante}」和「{cons}」陈列在邻近货架或同一区域，方便客户一次性取齐。",
        })

    if conf >= 0.40 and len(suggestions) == 0:
        suggestions.append({
            "type": "组合优惠",
            "priority": "中",
            "reason": f"置信度 {conf:.0%}，购买关联稳定。",
            "action": f"推出「{ante}+{cons}」组合价，用小幅折扣换取客单价提升。",
        })

    if lift >= 2.0 and len(suggestions) <= 1:
        suggestions.append({
            "type": "加价购",
            "priority": "中",
            "reason": f"提升度 {lift:.1f}，跨品类关联显著。",
            "action": f"购买「{ante}」后弹出加价换购「{cons}」的提示，加 XX 元即可获得。",
        })

    summary = ""
    if suggestions:
        summary = f"客户购买「{ante}」后，{conf:.0%} 的人会同时购买「{cons}」(比随机高 {lift:.1f} 倍)"
    if group_name:
        summary = f"[{group_name}] {summary}" if summary else f"[{group_name}]"

    return {
        "summary": summary,
        "suggestions": suggestions,
    }
