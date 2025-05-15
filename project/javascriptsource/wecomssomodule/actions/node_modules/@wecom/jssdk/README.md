# @wecom/jssdk

微信（企业微信）JSSDK，可用于替代 jweixin.js。

## 主要特性

1. 自动调用 config、agentConfig
2. API promise 化
3. 提供 ts 定义
4. 通过 npm 发布

## 使用方法

通过 npm 引入：

```js
import * as ww from '@wecom/jssdk'

// 注册应用信息
ww.register({
  corpId: 'ww7ca4776b2a70000',
  jsApiList: [
    'selectExternalContact',
  ],
  async getConfigSignature(url) {
    // 根据 url 生成 config 签名信息（需要开发者自行实现）
    // 返回 { timestamp, nonceStr, signature }
    return getJsApiSignature(url)
  }
})

// 可以立刻调用JS接口，无需等待ready回调
ww.selectExternalContact({
  success(res) {
    console.log(res.userIds[0])
  }
})
```

通过 script 标签引入：

```html
<script src="https://unpkg.com/@wecom/jssdk"></script>
<script>
  alert(ww.SDK_VERSION)
</script>
```

## API

常规接口可参考以下文档：

- [企业微信 JS-SDK 文档](https://developer.work.weixin.qq.com/document/path/98560)
- [微信 JS-SDK 说明文档](https://developers.weixin.qq.com/doc/offiaccount/OA_Web_Apps/JS-SDK.html)

所有命令接口均已 promise 化，具体用法请参考 ts 定义。

### ww.register(options)

- __参数：__
  - `{Object} options` 注册参数
- __说明：__

  注册应用信息，在调用其他JS接口前必须先调用该接口。

  在注册应用信息后，SDK会在需要的时候自动调用 `wx.config`，此时SDK会通过 `getConfigSignature` 等回调函数获取签名信息。

- __options 结构：__

  属性 | 类型 | 默认值 | 必填 | 说明
  --- | --- | --- | --- | ---
  corpId | string | | 是 | 当前用户所属企业ID（或公众号的 appId）
  agentId | number / string | | 否 | 企业微信第三方应用的AgentID
  jsApiList | Array&lt;string&gt; | [ "config" ] | 否 | 需要使用的JS接口列表
  getConfigSignature | Function | | 否 | config 签名生成函数，详见后续说明
  getAgentConfigSignature | Function | | 否 | agentConfig 签名生成函数，详见后续说明
  openTagList | Array&lt;string&gt; | | 否 | 需要使用的开放标签列表，例如 [ "wx-open-launch-app" ]
  onConfigSuccess | Function | | 否 | config 成功回调
  onConfigFail | Function | | 否 | config 失败回调
  onConfigComplete | Function | | 否 | config 完成回调
  onAgentConfigSuccess | Function | | 否 | agentConfig 成功回调
  onAgentConfigFail | Function | | 否 | agentConfig 失败回调
  onAgentConfigComplete | Function | | 否 | agentConfig 完成回调

- __getConfigSignature、getAgentConfigSignature 返回结构：__

  属性 | 类型 | 必填 | 说明
  --- | --- | --- | ---
  timestamp | number / string | 是 | 生成签名的时间戳
  nonceStr | string | 是 | 生成签名的随机串
  signature | string | 是 | 签名，生成方法见 [JS-SDK使用权限签名算法](https://open.work.weixin.qq.com/api/doc/90000/90136/90506)

- __示例代码：__

  ```js
  ww.register({
    corpId: 'ww7ca4776b2a70000',
    jsApiList: ['selectExternalContact'],
    async getConfigSignature(url) {
      /**
       * 根据 url 生成 config 签名
       */
      return { timestamp, nonceStr, signature }
    }
  })
  ```

- __注意：__

  - 企业自建应用只需要提供 `getConfigSignature`
  - 对第三方应用：
    - 在企业微信 3.0.24 及以后版本中，只需要提供 `getAgentConfigSignature`
    - 在其他环境下，必须同时提供 `getConfigSignature` 和 `getAgentConfigSignature`
  - 签名函数在页面URL发生变更后需要重新调用，对使用哈希路由的单页应用，签名函数只会被调用一次

### ww.initOpenData([options])

__注意：使用通讯录组件前仍需在页面上引入 https://open.work.weixin.qq.com/wwopen/js/jwxwork-1.0.0.js__

- __参数：__
  - `{Object} [options]` 通用回调参数
- __返回值：__ `Promise<Object>` 结构同 wx.agentConfig
- __说明：__

  初始化企业微信通讯录组件。在该接口返回成功后，可以直接调用 `WWOpenData.bind` 等方法。

- __options 结构：__

  属性 | 类型 | 默认值 | 必填 | 说明
  --- | --- | --- | --- | ---
  success | Function | | 否 | 成功回调
  fail | Function | | 否 | 失败回调
  complete | Function | | 否 | 完成回调

### ww.getSignature(options)

__注意：该接口仅用于本地调试，请勿在线上版本中使用__

- __参数：__
  - `{Object} options` 用于生成签名的参数，也可以直接传入 jsapi ticket
- __返回值：__ `{Object} result` 签名结果
- __说明：__

  根据提供的参数生成签名。若只传入 `ticket` 参数，则默认为当前页面生成签名。

- __options 结构：__

  属性 | 类型 | 默认值 | 必填 | 说明
  --- | --- | --- | --- | ---
  ticket | string | | 是 | 用于签名的 JSAPI Ticket
  nonceStr | string | 随机生成 | 否 | 生成签名的随机串
  timestamp | number | 取当前时间 | 否 | 生成签名的时间戳
  url | string | 取当前页面URL | 否 | 生成签名的URL

- __result 结构：__

  属性 | 类型 | 说明
  --- | --- | ---
  nonceStr | string | 生成签名的随机串
  timestamp | number | 生成签名的时间戳
  signature | string | 签名

- __示例代码：__

  ```js
  // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  // 该代码仅用于本地调试，请勿在生产环境对外暴露 JSAPI_TICKET
  // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  const JSAPI_TICKET = 'sM4AOVdWfPE4DxkXGEs8VMCPGGVi4C3VM0P37wVUCFvkVAy_90u5h9nbSlYy3-Sl-HhTdfl2fzFy1AOcHKP7qg'

  ww.register({
    corpId: 'ww7ca4776b2a70000',
    jsApiList: ['selectExternalContact'],
    getConfigSignature(url) {
      return ww.getSignature(JSAPI_TICKET)
    }
  })
  ```

### ww.on(name, callback)

- __参数：__
  - `{string} name` 监听的事件名称
  - `{Function} callback` 事件回调函数
- __返回值：__ `Promise<void>` 成功监听后返回
- __说明：__

  等待 WeixinJSBridgeReady 后调用 `WeixinJSBridge.on`。用于监听 SDK 没有定义的事件。

### ww.invoke(name, [params, [callback]])

- __参数：__
  - `{string} name` 调用的接口名称
  - `{Object} [params]` 接口传入参数
  - `{Function} [callback]` 回调函数
- __返回值：__ `Promise<unknown>`
- __说明：__

  等待 WeixinJSBridgeReady 后调用 `WeixinJSBridge.invoke`。用于调用 SDK 没有定义的接口。

### ww.onWeixinJSBridgeReady

- __类型：__ `Promise<void>`
- __说明：__

  等待 WeixinJSBridge 注入完成。

### ww.isWeixinJSBridgeReady

- __类型：__ `boolean`
- __说明：__

  当前 WeixinJSBridge 是否已注入。

### ww.ensureConfigReady()

- __返回值：__ `Promise<void>`
- __说明：__

  根据当前环境检查 config 或 agentConfig 的状态。若 config 状态已失效（url 发生变更），会重新触发 config 流程。
