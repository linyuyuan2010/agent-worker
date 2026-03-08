local redis = require "resty.redis"
local shared_data = ngx.shared.upstream_cache

local host = ngx.var.host
local cache_key = "proxy:" .. host

local target = shared_data:get(cache_key)

if not target then
    local red = redis:new()
    red:set_timeout(1000)
    local ok, err = red:connect("redis", 6379)
    
    if ok then
        target, err = red:get(host)
        if target and target ~= ngx.null then
            shared_data:set(cache_key, target, 60)
        end
    end
end

if not target or target == ngx.null then
    ngx.status = ngx.HTTP_NOT_FOUND
    ngx.say("No backend found for: ", host)
    ngx.exit(ngx.HTTP_NOT_FOUND)
end

ngx.var.target_url = target