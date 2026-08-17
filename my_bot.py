# Name: Heet
# College: DJSCE
# Roll Number: YOUR_ROLL_NUMBER

import random
class Bot:
    name = "OracleX"

    def reset(self, seat, config, seed):
        self.seat = seat
        self.config = config
        self.rng = random.Random(seed)
        self.opp_quotes = {}
        self.opp_wins = {}
        self.my_wins = {}
        self.last_value = 0

    def _opp_anchor(self, obs):
        if not self.opp_quotes:
            return None
        r = max(self.opp_quotes)
        return self.opp_quotes[r]

    def _value(self, obs, quote=None):
        mine = obs.k_mine

        if obs.foresight:
            return mine + sum(obs.foresight)

        if not obs.is_maker and quote is not None:
            mid = (quote[0] + quote[1]) / 2
            return mine + mid

        x = self._opp_anchor(obs)
        if x is not None:
            return mine + x

        return mine

    def _power_value(self, obs, name):
        r = obs.round

        if name == "FORESIGHT":
            vals = [0.85, 1.20, 1.55, 1.90, 2.15]
            return vals[r - 1]

        if name == "SUBSTITUTE":
            vals = [1.40, 1.15, 0.90, 0.55, 0.30]
            return vals[r - 1]

        if name == "TRICK_ROOM":
            vals = [1.20, 0.15, 0.20, 0.65, 0.55]
            return vals[r - 1]

        if name == "STEALTH_ROCK":
            vals = [1.45, 0.80, 0.75, 0.65, 0.0]
            return vals[r - 1]

        if name == "TRANSFORM":
            if abs(obs.k_mine) <= 1:
                return [1.45, 1.30, 1.20][r - 1]
            return 0.0

        return 0.0

    def _market_bid(self, obs, name):
        vals = []

        for x in obs.auction_log:
            if x["power"] == name:
                vals.append(x["cost"])

        if not vals:
            return None

        return vals[-1]

    def bid(self, obs, offered):
        if not offered or obs.te_mine <= 0:
            return {}

        name = offered[0]
        value = self._power_value(obs, name)

        if value <= 0:
            return {}

        fair = value / self.config.TE_SALVAGE

        market = self._market_bid(obs, name)

        if market is not None:
            target = market + 1

            if target < fair * 0.45:
                target = int(fair * 0.45)

            bid = int(min(target, fair * 0.75))
        else:
            bid = int(fair * 0.60)

        if obs.round >= 4 and name == "FORESIGHT":
            bid += 1

        if name == "SUBSTITUTE" and obs.round <= 2:
            bid += 1

        if name == "TRANSFORM":
            if abs(obs.k_mine) > 1:
                return {}

        bid = max(0, min(bid, obs.te_mine))

        if bid == 0:
            return {}

        return {name: bid}

    def quote(self, obs):
        value = round(self._value(obs))

        w = obs.final_cap

        lo = value - w // 2
        hi = lo + w

        return (lo, hi)

    def respond(self, obs, quote, turn):
        bid, ask = quote
        value = self._value(obs, quote)

        buy = value - ask
        sell = bid - value

        if "SUBSTITUTE" in obs.powers_mine:
            if buy > -0.8 and buy >= sell:
                return "ACCEPT_BUY"
            if sell > -0.8:
                return "ACCEPT_SELL"
        else:
            if buy > 0 and buy >= sell:
                return "ACCEPT_BUY"

            if sell > 0:
                return "ACCEPT_SELL"

        width = ask - bid

        if turn == obs.n_turns:
            mid = (bid + ask) // 2

            if "TRICK_ROOM" in obs.powers_mine:
                if value > mid + 1:
                    return "ACCEPT_BUY"

            if "STEALTH_ROCK" in obs.powers_mine:
                if value > mid + 1:
                    return "ACCEPT_BUY"

            if value <= bid:
                return "ACCEPT_SELL"

            if value >= ask:
                return "ACCEPT_BUY"

        new_width = max(
            obs.final_cap,
            width - self.config.MIN_REDUCTION
        )

        center = round(value)

        left = center - new_width // 2
        right = left + new_width

        left = max(bid, left)
        right = min(ask, right)

        if right - left < new_width:
            left = ask - new_width
            right = ask

        return ("COUNTER", left, right)

    def use_transform(self, obs):
        return abs(obs.k_mine) <= 1
