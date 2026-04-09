# -*- coding: utf-8 -*-
"""将 script.js 中所有 mock 登录/注册/联系/报告代码替换为真实 API 调用"""

import os

JS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'script.js')
print(f'Processing: {JS_FILE}')

with open(JS_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

replaced = {}

# ============================================================
# 1. 替换 initLoginPage() 登录 mock（12格缩进，注释：// 模拟登录验证）× 2
# ============================================================
old = (
    "            // 模拟登录验证\n"
    "            setTimeout(() => {\n"
    "                const user = DataService.users.find(u => u.email === email && u.password === password);\n"
    "                if (user) {\n"
    "                    // 保存登录状态\n"
    "                    localStorage.setItem('carbon_platform_logged_in', 'true');\n"
    "                    if (rememberMe) {\n"
    "                        localStorage.setItem('carbon_platform_remember_email', email);\n"
    "                    }\n"
    "                    \n"
    "                    // 保存用户信息\n"
    "                    PlatformState.user = {\n"
    "                        id: user.id,\n"
    "                        email: user.email,\n"
    "                        name: user.name,\n"
    "                        company: user.company,\n"
    "                        type: user.type,\n"
    "                        loginTime: new Date().toISOString()\n"
    "                    };\n"
    "                    saveUserData();\n"
    "                    \n"
    "                    // 刷新页面状态\n"
    "                    checkLoginStatus();\n"
    "                    showToast(`登录成功！欢迎回来，${user.name}`, 'success');\n"
    "                    \n"
    "                    // 初始化平台功能\n"
    "                    initPlatform();\n"
    "                } else {\n"
    "                    showToast('邮箱或密码错误，请重试', 'error');\n"
    "                }\n"
    "                \n"
    "                loginBtn.innerHTML = originalText;\n"
    "                loginBtn.disabled = false;\n"
    "            }, 1500);"
)
new = (
    "            // 调用后端API登录\n"
    "            API.login(email, password).then(data => {\n"
    "                localStorage.setItem('carbon_platform_logged_in', 'true');\n"
    "                if (rememberMe) {\n"
    "                    localStorage.setItem('carbon_platform_remember_email', email);\n"
    "                }\n"
    "                PlatformState.user = {\n"
    "                    id: data.user.id,\n"
    "                    email: data.user.email,\n"
    "                    name: data.user.name,\n"
    "                    company: data.user.company || '',\n"
    "                    type: data.user.company_type || 'ecommerce',\n"
    "                    loginTime: new Date().toISOString()\n"
    "                };\n"
    "                saveUserData();\n"
    "                checkLoginStatus();\n"
    "                showToast(`登录成功！欢迎回来，${data.user.name}`, 'success');\n"
    "                initPlatform();\n"
    "            }).catch(err => {\n"
    "                showToast(err.message || '邮箱或密码错误，请重试', 'error');\n"
    "            }).finally(() => {\n"
    "                loginBtn.innerHTML = originalText;\n"
    "                loginBtn.disabled = false;\n"
    "            });"
)
replaced['login_initLoginPage'] = content.count(old)
content = content.replace(old, new)

# ============================================================
# 2. 替换 initLoginPage() 注册 mock（12格缩进，注释：// 模拟注册）× 2
# ============================================================
old = (
    "            // 模拟注册\n"
    "            setTimeout(() => {\n"
    "                const existingUser = DataService.users.find(u => u.email === email);\n"
    "                if (existingUser) {\n"
    "                    showToast('该邮箱已被注册', 'error');\n"
    "                    registerBtn.innerHTML = originalText;\n"
    "                    registerBtn.disabled = false;\n"
    "                    return;\n"
    "                }\n"
    "                \n"
    "                // 添加新用户\n"
    "                const newUser = {\n"
    "                    id: DataService.users.length + 1,\n"
    "                    email,\n"
    "                    password,\n"
    "                    name,\n"
    "                    company,\n"
    "                    type: 'ecommerce'\n"
    "                };\n"
    "                DataService.users.push(newUser);\n"
    "                \n"
    "                // 自动登录\n"
    "                localStorage.setItem('carbon_platform_logged_in', 'true');\n"
    "                PlatformState.user = {\n"
    "                    id: newUser.id,\n"
    "                    email: newUser.email,\n"
    "                    name: newUser.name,\n"
    "                    company: newUser.company,\n"
    "                    type: newUser.type,\n"
    "                    loginTime: new Date().toISOString()\n"
    "                };\n"
    "                saveUserData();\n"
    "                \n"
    "                checkLoginStatus();\n"
    "                showToast(`注册成功！欢迎加入碳融智核，${name}`, 'success');\n"
    "                initPlatform();\n"
    "                \n"
    "                registerBtn.innerHTML = originalText;\n"
    "                registerBtn.disabled = false;\n"
    "            }, 2000);"
)
new = (
    "            // 调用后端API注册\n"
    "            API.register({ name, company, email, password }).then(data => {\n"
    "                localStorage.setItem('carbon_platform_logged_in', 'true');\n"
    "                PlatformState.user = {\n"
    "                    id: data.user.id,\n"
    "                    email: data.user.email,\n"
    "                    name: data.user.name,\n"
    "                    company: data.user.company || '',\n"
    "                    type: data.user.company_type || 'ecommerce',\n"
    "                    loginTime: new Date().toISOString()\n"
    "                };\n"
    "                saveUserData();\n"
    "                checkLoginStatus();\n"
    "                showToast(`注册成功！欢迎加入碳融智核，${data.user.name}`, 'success');\n"
    "                initPlatform();\n"
    "            }).catch(err => {\n"
    "                showToast(err.message || '注册失败，请重试', 'error');\n"
    "            }).finally(() => {\n"
    "                registerBtn.innerHTML = originalText;\n"
    "                registerBtn.disabled = false;\n"
    "            });"
)
replaced['register_initLoginPage'] = content.count(old)
content = content.replace(old, new)

# ============================================================
# 3. 替换 initLoginForm() 中的 mock 登录（8格缩进，注释：// 模拟API调用）
# ============================================================
old = (
    "        // 模拟API调用\n"
    "        setTimeout(() => {\n"
    "            const user = DataService.users.find(u => u.email === email && u.password === password);\n"
    "            \n"
    "            if (user) {\n"
    "                PlatformState.user = {\n"
    "                    id: user.id,\n"
    "                    email: user.email,\n"
    "                    name: user.name,\n"
    "                    company: user.company,\n"
    "                    type: user.type,\n"
    "                    loginTime: new Date().toISOString()\n"
    "                };\n"
    "                \n"
    "                saveUserData();\n"
    "                updateUserUI();\n"
    "                \n"
    "                // 关闭模态框\n"
    "                const modal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));\n"
    "                modal.hide();\n"
    "                \n"
    "                showToast(`欢迎回来，${user.name}！`, 'success');\n"
    "            } else {\n"
    "                showToast('邮箱或密码错误，请重试', 'error');\n"
    "            }\n"
    "            \n"
    "            loginBtn.innerHTML = originalText;\n"
    "            loginBtn.disabled = false;\n"
    "            loginForm.reset();\n"
    "        }, 1500);"
)
new = (
    "        // 调用后端API登录\n"
    "        API.login(email, password).then(data => {\n"
    "            localStorage.setItem('carbon_platform_logged_in', 'true');\n"
    "            PlatformState.user = {\n"
    "                id: data.user.id,\n"
    "                email: data.user.email,\n"
    "                name: data.user.name,\n"
    "                company: data.user.company || '',\n"
    "                type: data.user.company_type || 'ecommerce',\n"
    "                loginTime: new Date().toISOString()\n"
    "            };\n"
    "            saveUserData();\n"
    "            updateUserUI();\n"
    "            const modal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));\n"
    "            if (modal) modal.hide();\n"
    "            checkLoginStatus();\n"
    "            showToast(`欢迎回来，${data.user.name}！`, 'success');\n"
    "        }).catch(err => {\n"
    "            showToast(err.message || '邮箱或密码错误，请重试', 'error');\n"
    "        }).finally(() => {\n"
    "            loginBtn.innerHTML = originalText;\n"
    "            loginBtn.disabled = false;\n"
    "            loginForm.reset();\n"
    "        });"
)
replaced['login_initLoginForm'] = content.count(old)
content = content.replace(old, new)

# ============================================================
# 4. 替换 initRegisterForm() 中的 mock 注册（注释：// 模拟API调用）
# ============================================================
old = (
    "        // 模拟API调用\n"
    "        setTimeout(() => {\n"
    "            // 检查邮箱是否已存在\n"
    "            const existingUser = DataService.users.find(u => u.email === email);\n"
    "            if (existingUser) {\n"
    "                showToast('该邮箱已被注册，请使用其他邮箱', 'error');\n"
    "                registerBtn.innerHTML = originalText;\n"
    "                registerBtn.disabled = false;\n"
    "                return;\n"
    "            }\n"
    "            \n"
    "            // 创建新用户\n"
    "            const newUser = {\n"
    "                id: DataService.users.length + 1,\n"
    "                email,\n"
    "                password,\n"
    "                name,\n"
    "                company,\n"
    "                type: 'ecommerce',\n"
    "                createdAt: new Date().toISOString()\n"
    "            };\n"
    "            \n"
    "            PlatformState.user = {\n"
    "                id: newUser.id,\n"
    "                email: newUser.email,\n"
    "                name: newUser.name,\n"
    "                company: newUser.company,\n"
    "                type: newUser.type,\n"
    "                loginTime: new Date().toISOString()\n"
    "            };\n"
    "            \n"
    "            saveUserData();\n"
    "            updateUserUI();\n"
    "            \n"
    "            // 关闭模态框\n"
    "            const modal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));\n"
    "            modal.hide();\n"
    "            \n"
    "            showToast(`注册成功！欢迎加入碳融智核，${name}！`, 'success');\n"
    "            \n"
    "            registerBtn.innerHTML = originalText;\n"
    "            registerBtn.disabled = false;\n"
    "            registerForm.reset();\n"
    "            \n"
    "            // 切换到登录标签\n"
    "            document.querySelector('.login-tab[data-tab=\"login\"]').click();\n"
    "        }, 2000);"
)
new = (
    "        // 调用后端API注册\n"
    "        API.register({ name, company, email, password }).then(data => {\n"
    "            localStorage.setItem('carbon_platform_logged_in', 'true');\n"
    "            PlatformState.user = {\n"
    "                id: data.user.id,\n"
    "                email: data.user.email,\n"
    "                name: data.user.name,\n"
    "                company: data.user.company || '',\n"
    "                type: data.user.company_type || 'ecommerce',\n"
    "                loginTime: new Date().toISOString()\n"
    "            };\n"
    "            saveUserData();\n"
    "            updateUserUI();\n"
    "            const modal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));\n"
    "            if (modal) modal.hide();\n"
    "            checkLoginStatus();\n"
    "            showToast(`注册成功！欢迎加入碳融智核，${data.user.name}！`, 'success');\n"
    "        }).catch(err => {\n"
    "            showToast(err.message || '注册失败，请重试', 'error');\n"
    "        }).finally(() => {\n"
    "            registerBtn.innerHTML = originalText;\n"
    "            registerBtn.disabled = false;\n"
    "            registerForm.reset();\n"
    "        });"
)
replaced['register_initRegisterForm'] = content.count(old)
content = content.replace(old, new)

# ============================================================
# 5. 替换 initContactForm() 中的 mock（注释：// 模拟API调用）
# ============================================================
old = (
    "        // 模拟API调用\n"
    "        setTimeout(() => {\n"
    "            showToast('咨询提交成功！我们的客服将在24小时内联系您。', 'success');\n"
    "            submitBtn.innerHTML = originalText;\n"
    "            submitBtn.disabled = false;\n"
    "            contactForm.reset();\n"
    "            \n"
    "            // 关闭模态框\n"
    "            const modal = bootstrap.Modal.getInstance(document.getElementById('contactModal'));\n"
    "            modal.hide();\n"
    "        }, 1500);"
)
new = (
    "        // 调用后端API提交联系表单\n"
    "        const formData = {\n"
    "            name: contactForm.querySelector('[name=\"contact_name\"], input[placeholder*=\"姓名\"]')?.value || '',\n"
    "            company: contactForm.querySelector('[name=\"contact_company\"], input[placeholder*=\"企业\"]')?.value || '',\n"
    "            phone: contactForm.querySelector('[name=\"contact_phone\"], input[type=\"tel\"]')?.value || '',\n"
    "            email: contactForm.querySelector('[name=\"contact_email\"], input[type=\"email\"]')?.value || '',\n"
    "            message: contactForm.querySelector('[name=\"message\"], textarea')?.value || '',\n"
    "            company_type: contactForm.querySelector('[name=\"company_type\"], select')?.value || ''\n"
    "        };\n"
    "        API.submitContact(formData).then(() => {\n"
    "            showToast('咨询提交成功！我们的客服将在24小时内联系您。', 'success');\n"
    "            contactForm.reset();\n"
    "            const modal = bootstrap.Modal.getInstance(document.getElementById('contactModal'));\n"
    "            if (modal) modal.hide();\n"
    "        }).catch(err => {\n"
    "            showToast(err.message || '提交失败，请稍后重试', 'error');\n"
    "        }).finally(() => {\n"
    "            submitBtn.innerHTML = originalText;\n"
    "            submitBtn.disabled = false;\n"
    "        });"
)
replaced['contact_form'] = content.count(old)
content = content.replace(old, new)

# ============================================================
# 6. 替换 generateReport() 中的 mock（setTimeout 模拟）
# ============================================================
old = (
    "    // 模拟生成过程\n"
    "    setTimeout(() => {\n"
    "        const reportId = 'REPORT-' + Date.now().toString().slice(-8);\n"
    "        const generationTime = Math.floor(Math.random() * 10) + template.estimatedTime;\n"
    "        \n"
    "        // 创建报告记录\n"
    "        const report = {\n"
    "            id: reportId,\n"
    "            template: templateType,\n"
    "            name: `${template.name} - ${new Date().toLocaleDateString()}`,\n"
    "            generatedAt: new Date().toISOString(),\n"
    "            generationTime: generationTime,\n"
    "            wordCount: template.wordCount + Math.floor(Math.random() * 500),\n"
    "            charts: template.charts,\n"
    "            status: 'completed'\n"
    "        };\n"
    "        \n"
    "        // 保存到历史\n"
    "        PlatformState.reportHistory.unshift(report);\n"
    "        saveUserData();"
)
new = (
    "    // 调用后端API生成报告\n"
    "    API.generateReport({\n"
    "        template_type: templateType,\n"
    "        title: `${template.name} - ${new Date().toLocaleDateString()}`\n"
    "    }).then(report => {\n"
    "        const reportId = report.report_no || ('REPORT-' + Date.now().toString().slice(-8));\n"
    "        const generationTime = report.generation_time || template.estimatedTime;\n"
    "        // 保存到本地历史\n"
    "        PlatformState.reportHistory.unshift({\n"
    "            id: reportId,\n"
    "            dbId: report.id,\n"
    "            template: templateType,\n"
    "            name: report.title || `${template.name} - ${new Date().toLocaleDateString()}`,\n"
    "            generatedAt: report.created_at || new Date().toISOString(),\n"
    "            generationTime: generationTime,\n"
    "            wordCount: report.word_count || template.wordCount,\n"
    "            charts: report.charts_count || template.charts,\n"
    "            status: 'completed'\n"
    "        });\n"
    "        saveUserData();"
)
replaced['generate_report'] = content.count(old)
content = content.replace(old, new)

# 同时替换 generateReport 中 setTimeout 的结束部分（对应修改）
old2 = (
    "        showToast(`报告生成完成！编号: ${reportId}`, 'success');\n"
    "    }, template.estimatedTime * 1000);"
)
new2 = (
    "        showToast(`报告生成完成！编号: ${reportId}`, 'success');\n"
    "    }).catch(err => {\n"
    "        if (reportPreview) reportPreview.innerHTML = `<div class=\"alert alert-danger\"><i class=\"fas fa-exclamation-circle me-2\"></i>${err.message || '报告生成失败，请稍后重试'}</div>`;\n"
    "        showToast(err.message || '报告生成失败', 'error');\n"
    "    });"
)
replaced['generate_report_end'] = content.count(old2)
content = content.replace(old2, new2)

print('Replacement results:', replaced)

# 修复 logout 处理器（两处相同，统一添加 API.logout()）
old_logout = (
    "        logoutBtn.addEventListener('click', function(e) {\n"
    "            e.preventDefault();\n"
    "            localStorage.removeItem('carbon_platform_logged_in');\n"
    "            PlatformState.user = null;\n"
    "            checkLoginStatus();\n"
    "            showToast('已成功退出登录', 'success');\n"
    "        });"
)
new_logout = (
    "        logoutBtn.addEventListener('click', function(e) {\n"
    "            e.preventDefault();\n"
    "            API.logout();\n"
    "            localStorage.removeItem('carbon_platform_logged_in');\n"
    "            PlatformState.user = null;\n"
    "            checkLoginStatus();\n"
    "            showToast('已成功退出登录', 'success');\n"
    "        });"
)
logout_count = content.count(old_logout)
content = content.replace(old_logout, new_logout)
print(f'Logout handlers fixed: {logout_count}')

# 验证
remaining_mock = content.count('DataService.users.find(u => u.email === email')
print(f'Remaining mock login/register calls: {remaining_mock}')
print(f'API.login calls: {content.count("API.login(")}')
print(f'API.register calls: {content.count("API.register(")}')
print(f'API.submitContact calls: {content.count("API.submitContact(")}')
print(f'API.generateReport calls: {content.count("API.generateReport(")}')
print(f'API.logout calls: {content.count("API.logout()")}')

with open(JS_FILE, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
